# =========================================================================
# COINPILOT AI — EDITOR PERIODÍSTICO Y GENERADOR DE REPORTES PDF
# =========================================================================
import os
import json
import sys
import smtplib
import feedparser
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from email.message import EmailMessage

# Intentar instalar ReportLab si falta para asegurar la maquetación en PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "reportlab"])
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

# --- CONFIGURACIÓN DE ENVÍO Y RUTAS ---
CORREO_EMISOR = "mcserviceai@gmail.com"
CONTRASENA_APP = "1818bake"
CORREO_DESTINATARIO = "mcserviceia@gmail.com"

CARPETA_AI = Path("/content/drive/MyDrive/CoinPilotAI")
ARCHIVO_GUARDIAN = CARPETA_AI / "guardian.json"
ARCHIVO_PDF = CARPETA_AI / "CoinPilot_Daily_Newspaper.pdf"

# --- RECOPILACIÓN DE DATOS (MACRO, MICRO Y FINANZAS) ---
def obtener_datos_financieros():
    activos = {"SPY": "S&P 500", "IWM": "Small Caps (IWM)", "BTC-USD": "Bitcoin", "GLD": "Oro"}
    datos = yf.download(list(activos.keys()), period="5d", interval="1d", auto_adjust=True, progress=False)
    cierre = datos["Close"].ffill()
    
    resumen = []
    for ticker, nombre in activos.items():
        serie = cierre[ticker].dropna()
        if not serie.empty:
            precio_actual = serie.iloc[-1]
            precio_previo = serie.iloc[-2] if len(serie) > 1 else precio_actual
            var_pct = ((precio_actual / precio_previo) - 1) * 100
            resumen.append({"Activo": nombre, "Precio": f"{precio_actual:,.2f}", "Var %": f"{var_pct:+.2f}%"})
    return resumen

def obtener_noticias_rss():
    urls = {
        "Macro": "https://news.google.com/rss/search?q=stock+market+OR+economy&hl=es-419&gl=US&ceid=US:es",
        "Small_Caps": "https://news.google.com/rss/search?q=small+cap+companies+OR+IWM&hl=es-419&gl=US&ceid=US:es",
        "Crypto": "https://news.google.com/rss/search?q=crypto+regulation+OR+bitcoin&hl=es-419&gl=US&ceid=US:es"
    }
    
    noticias = {}
    for categoria, url in urls.items():
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:4]:
            items.append({"titulo": entry.title, "enlace": entry.link})
        noticias[categoria] = items
    return noticias

def cargar_estado_guardian():
    if ARCHIVO_GUARDIAN.is_file():
        try:
            return json.loads(ARCHIVO_GUARDIAN.read_text(encoding="utf-8block"))
        except:
            pass
    return {"bloqueado": False, "motivo": "N/A", "maximo_patrimonio": 1000.0}

# --- GENERACIÓN DEL PERIÓDICO EN PDF ---
def generar_pdf_periodico():
    doc = SimpleDocTemplate(str(ARCHIVO_PDF), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados estilo Periódico/Newsletter
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=colors.HexColor("#1a252f"), alignment=1)
    style_subtitle = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=10, leading=14, textColor=colors.HexColor("#7f8c8d"), alignment=1)
    style_h2 = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor("#2c3e50"), spaceBefore=12, spaceAfter=6)
    style_body = ParagraphStyle('BodyText', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor("#34495e"))
    
    story = []
    
    # Cabecera del Periódico
    story.append(Paragraph("COINPILOT FINANCIAL TIMES", style_title))
    story.append(Paragraph(f"Boletín Económico y de Gestión de Riesgo | {datetime.now().strftime('%d de %B, %Y')}", style_subtitle))
    story.append(Spacer(1, 10))
    
    # Línea divisoria de estilo prensa
    line_table = Table([[""]], colWidths=[540], rowHeights=[2])
    line_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1a252f"))]))
    story.append(line_table)
    story.append(Spacer(1, 15))
    
    # Sección 1: Estado del Guardián de Riesgos
    story.append(Paragraph("🛡️ ESTADO DEL GUARDIÁN Y CONTROL DE CAPITAL", style_h2))
    g_state = cargar_estado_guardian()
    bloq_txt = "SISTEMA BLOQUEADO ⛔ (Preservación Activa)" if g_state.get("bloqueado") else "OPERATIVA NORMAL ✅ (Estable)"
    g_txt = f"<b>Estado actual:</b> {bloq_txt}<br/>"\
            f"<b>Patrimonio Máximo Histórico:</b> {g_state.get('maximo_patrimonio', 1000.0):.2f} EUR<br/>"\
            f"<b>Motivo de Alerta:</b> {g_state.get('motivo', 'Ninguno registrado')}"
    story.append(Paragraph(g_txt, style_body))
    story.append(Spacer(1, 15))
    
    # Sección 2: Tablas de Mercado
    story.append(Paragraph("📊 RESUMEN DIARIO DE MERCADOS", style_h2))
    datos_fin = obtener_datos_financieros()
    tabla_datos = [["Activo", "Precio Cierre", "Variación Diaria"]]
    for d in datos_fin:
        tabla_datos.append([d["Activo"], d["Precio"], d["Var %"]])
        
    t = Table(tabla_datos, colWidths=[180, 180, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#bdc3c7")),
        ('FONTSIZE', (0,0), (-1,-1), 9)
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    # Sección 3: Noticias Internacionales y Pequeñas Empresas
    story.append(Paragraph("📰 SECCIÓN INFORMATIVA MACRO Y PEQUEÑAS EMPRESAS", style_h2))
    news = obtener_noticias_rss()
    
    news_html = ""
    for cat, items in news.items():
        news_html += f"<b>• CATEGORÍA: {cat.upper()}</b><br/>"
        for idx, item in enumerate(items, 1):
            news_html += f"{idx}. {item['titulo']}<br/><i>Fuente: Google News RSS</i><br/><br/>"
            
    story.append(Paragraph(news_html, style_body))
    
    doc.build(story)
    print("✅ Periódico digital PDF compilado exitosamente.")

# --- PROTOCOLO DE ENVÍO DE CORREO ---
def enviar_periodico_correo():
    generar_pdf_periodico()
    
    msg = EmailMessage()
    msg["Subject"] = f"📰 Periódico CoinPilot AI - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = CORREO_EMISOR
    msg["To"] = CORREO_DESTINATARIO
    msg.set_content("Hola,\n\nAdjunto encontrarás tu edición diaria del periódico financiero de CoinPilot AI con el resumen económico, análisis de pequeñas empresas y estado del guardián.\n\nUn saludo.\nCoinPilot Risk Engine")
    
    # Adjuntar PDF
    if ARCHIVO_PDF.is_file():
        with open(ARCHIVO_PDF, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=ARCHIVO_PDF.name)
            
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(CORREO_EMISOR, CONTRASENA_APP)
            server.send_message(msg)
        print(f"✅ Periódico diario enviado exitosamente a {CORREO_DESTINATARIO}")
    except Exception as e:
        print(f"⚠️ Error al enviar el correo: {e}")

if __name__ == "__main__":
    enviar_periodico_correo()
