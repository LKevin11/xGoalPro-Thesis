import sys
import threading
import asyncio
from qasync import QEventLoop

from PyQt5.QtWidgets import QApplication

from Application import App


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Initialize the application asynchronously
        main_app = App()

        app.aboutToQuit.connect(loop.stop)

        with loop:
            try:
                loop.run_forever()
            finally:
                loop.run_until_complete(main_app.close_app())
                loop.close()
                print(">>> Checking pending tasks & threads on exit")

                # Any asyncio tasks still alive?
                pending = asyncio.all_tasks(loop)
                if pending:
                    print("Pending asyncio tasks:", pending)
                    for task in pending:
                        task.cancel()
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                # Any threads still running?
                print("Active threads:", threading.enumerate())
    except asyncio.exceptions.CancelledError:
        pass  # This is normal when closing the application
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)
