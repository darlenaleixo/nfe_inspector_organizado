from apscheduler.schedulers.background import BackgroundScheduler
from cert.manager import CertificateManager
from cert.config import PFX_PATH, PFX_PASSWORD, ALERT_DAYS_BEFORE, CHECK_INTERVAL_HOURS
from cert.utils import send_email_alert

def check_certificate():
    mgr = CertificateManager(PFX_PATH, PFX_PASSWORD)
    dias = mgr.days_until_expiration()
    if dias <= ALERT_DAYS_BEFORE:
        send_email_alert(dias)

def start_scheduler():
    sched = BackgroundScheduler()
    sched.add_job(check_certificate, 'interval', hours=CHECK_INTERVAL_HOURS)
    sched.start()
