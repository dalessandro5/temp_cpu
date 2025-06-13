# temperatura_win.py - Monitor CPU con envío por correo
import os
import platform
import subprocess
from datetime import datetime
import smtplib
from email.message import EmailMessage

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class MonitorCPUWindows:
    def __init__(self):
        self.system = platform.system()
        self.cpu_name = self.get_cpu_name()
        self.psutil_available = PSUTIL_AVAILABLE

    def get_cpu_name(self):
        try:
            result = subprocess.run([
                'wmic', 'cpu', 'get', 'name', '/value'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'Name=' in line and line.split('=')[1].strip():
                        return line.split('=')[1].strip()
            return platform.processor() or "AMD Ryzen 5 5500U"
        except:
            return platform.processor() or "CPU no identificado"

    def estimate_temperature_from_cpu_usage(self):
        if not self.psutil_available:
            return None
        try:
            usage_samples = []
            for _ in range(3):
                usage = psutil.cpu_percent(interval=0.5)
                usage_samples.append(usage)
            avg_usage = sum(usage_samples) / len(usage_samples)
            base_temp = 35
            usage_factor = avg_usage * 0.3
            estimated_temp = base_temp + usage_factor
            return {
                'sensor': 'Estimación basada en uso de CPU',
                'temp': estimated_temp
            }
        except:
            return None

    def get_cpu_stats_psutil(self):
        if not self.psutil_available:
            return {}

        try:
            stats = {}
            stats['usage_total'] = psutil.cpu_percent(interval=1)
            stats['usage_per_core'] = psutil.cpu_percent(percpu=True, interval=0.1)
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                stats['frequency'] = {
                    'current': cpu_freq.current,
                    'min': cpu_freq.min,
                    'max': cpu_freq.max
                }
            memory = psutil.virtual_memory()
            stats['memory'] = {
                'total': memory.total / (1024**3),
                'used': memory.used / (1024**3),
                'percent': memory.percent
            }
            return stats
        except:
            return {}

    def show_header(self):
        print("=" * 70)
        print("MONITOR DE TEMPERATURA CPU - WINDOWS EDITION")
        print("=" * 70)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sistema: {self.system} {platform.release()}")
        print(f"Procesador: {self.cpu_name}")
        print("=" * 70)

    def show_temperature_analysis(self):
        estimation = self.estimate_temperature_from_cpu_usage()
        if estimation:
            print(f"Temperatura estimada: {estimation['temp']:.1f}°C")
        else:
            print("No fue posible estimar la temperatura.")
        return estimation

    def show_system_performance(self):
        stats = self.get_cpu_stats_psutil()
        if stats:
            print(f"Uso total de CPU: {stats['usage_total']}%")
            print(f"Memoria usada: {stats['memory']['used']:.1f}GB / {stats['memory']['total']:.1f}GB")
            print("Uso por núcleo:")
            for i, usage in enumerate(stats['usage_per_core'][:8]):
                print(f"  Núcleo {i}: {usage:.1f}%")
        else:

            print("No se pudo obtener estadísticas del sistema.")
def enviar_email(temperatura, destinatario, remitente, clave_app):
    mensaje = EmailMessage()
    mensaje['Subject'] = 'Temperatura CPU - Reporte'
    mensaje['From'] = remitente
    mensaje['To'] = destinatario

    cuerpo = f"""\
Reporte generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Temperatura estimada: {temperatura:.1f}°C

Este es un mensaje automático del monitor de temperatura.
"""
    mensaje.set_content(cuerpo)

    try:
        print("Conectando al servidor SMTP...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            print("Conexión establecida. Autenticando...")
            smtp.login(remitente, clave_app)
            print("Autenticado. Enviando correo...")
            smtp.send_message(mensaje)
        print("Correo enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def main():
    monitor = MonitorCPUWindows()
    try:
        monitor.show_header()
        estimation = monitor.show_temperature_analysis()
        monitor.show_system_performance()
        print("=" * 70)
        print("Análisis completado")

        if estimation:
            temperatura = estimation['temp']
            remitente = os.getenv("REMITENTE_CORREO")
            clave_app = os.getenv("PASSWORD_CORREO")  # Clave de aplicación válida
            destinatario = os.getenv("REMITENTE_CORREO")
            enviar_email(temperatura, destinatario, remitente, clave_app)

    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}")

if __name__ == "__main__":
    main()
