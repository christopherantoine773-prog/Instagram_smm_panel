from django.core.management.base import BaseCommand
import panel.worker

class Command(BaseCommand):
    help = "Runs the SMM Panel background automation task worker queue"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("[WORKER] Launching SMM Panel queue worker process..."))
        self.stdout.write(self.style.NOTICE("Press Ctrl+C to terminate the process cleanly."))
        
        try:
            panel.worker._worker_running = True
            panel.worker.worker_loop()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("[WORKER] Worker process terminated by user."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[WORKER] Critical error: {e}"))
