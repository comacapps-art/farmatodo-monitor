import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import db_manager

def send_daily_report():
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    recipient = os.environ.get('RECIPIENT_EMAIL', 'coordinador.inteligencia_neg@distrilabve.com')
    
    if not smtp_user or not smtp_pass:
        print("Error: Credenciales SMTP no configuradas. No se puede enviar el correo.")
        return
        
    print(f"Preparando reporte diario para {recipient}...")
    
    # Check alerts from the last 24 hours
    db = db_manager.get_db()
    if not db:
        print("No se pudo conectar a la base de datos.")
        return
        
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d %H:%M:%S')
    
    alerts_ref = db.collection('alerts').where('timestamp', '>=', yesterday_str).stream()
    alerts = [doc.to_dict() for doc in alerts_ref]
    
    if not alerts:
        print("No hubo cambios de precio hoy. No se enviará correo.")
        return
        
    # Construir el correo en HTML
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #1e3a8a;">Reporte Diario de Monitoreo de Precios</h2>
        <p>El robot ha detectado <strong>{len(alerts)}</strong> cambios de precio en las últimas 24 horas.</p>
        <table border="1" style="border-collapse: collapse; width: 100%; text-align: left;">
          <thead>
            <tr style="background-color: #f1f5f9;">
              <th style="padding: 10px;">Fecha/Hora</th>
              <th style="padding: 10px;">SKU</th>
              <th style="padding: 10px;">Producto</th>
              <th style="padding: 10px;">Precio Anterior</th>
              <th style="padding: 10px;">Precio Nuevo</th>
              <th style="padding: 10px;">Tendencia</th>
            </tr>
          </thead>
          <tbody>
    """
    
    for a in alerts:
        is_up = a.get('direction') == 'up'
        color = "#ef4444" if is_up else "#10b981"
        icon = "📈" if is_up else "📉"
        
        html_content += f"""
            <tr>
              <td style="padding: 8px;">{a.get('timestamp')}</td>
              <td style="padding: 8px;"><strong>{a.get('sku')}</strong></td>
              <td style="padding: 8px;">{a.get('title')}</td>
              <td style="padding: 8px; text-decoration: line-through; color: #666;">{a.get('old_price')}</td>
              <td style="padding: 8px; font-weight: bold; color: {color};">{a.get('new_price')}</td>
              <td style="padding: 8px; color: {color};">{icon}</td>
            </tr>
        """
        
    html_content += """
          </tbody>
        </table>
        <p style="margin-top: 20px; font-size: 12px; color: #666;">Generado automáticamente por tu Robot de Monitoreo.</p>
      </body>
    </html>
    """
    
    # Send email
    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"Alerta de Precios - {len(alerts)} cambios detectados"
    msg['From'] = smtp_user
    msg['To'] = recipient
    
    part = MIMEText(html_content, 'html')
    msg.attach(part)
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(smtp_user, smtp_pass)
        
        # Soportar múltiples destinatarios si están separados por coma
        recipients_list = [r.strip() for r in recipient.split(',')]
        
        server.sendmail(smtp_user, recipients_list, msg.as_string())
        server.quit()
        print(f"Reporte enviado exitosamente a {recipient}")
    except Exception as e:
        print(f"Error enviando correo: {e}")

if __name__ == "__main__":
    send_daily_report()
