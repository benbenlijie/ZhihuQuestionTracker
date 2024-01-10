import time
from threading import Thread, Event


class DataTracker(Thread):
    """
    DataTracker 类负责定时调用 scrapper 的 fetch_data 函数来获取新数据，
    并将数据更新到 DataManager 中。

    功能细节：
    - 继承自 threading.Thread，使得定时任务可以在后台独立线程中运行。
    - 初始化时可配置调用 fetch_data 函数的时间间隔。
    - 在每次获取新的问题数据后，会调用 DataManager 实例的 update_questions 方法进行数据更新。
    - 在控制台输出每次调用的时间和更新情况，以便跟踪状态和潜在问题。

    使用方法:
    1. 创建 DataTracker 实例，提供 fetch_data 函数、DataManager 实例和间隔时间。
    2. 调用 start() 方法启动定时任务。
    3. 调用 stop() 方法停止定时任务。

    示例:
    ```
    tracker = DataTracker(fetch_data=fetch_data_function, data_manager=data_manager_instance, interval=60*5)
    tracker.start()
    # 当不再需要追踪数据时
    tracker.stop()
    ```
    """

    def __init__(self, fetch_data, data_manager, interval):
        """
        初始化 DataTracker 对象。

        :param fetch_data: 可调用对象，应当返回新抓取的问题数据列表。
        :param data_manager: DataManager 实例，用于管理问题数据。
        :param interval: 调用 fetch_data 函数的时间间隔（秒）。
        """
        super().__init__()
        self.fetch_data = fetch_data
        self.data_manager = data_manager
        self.interval = interval
        self.stop_event = Event()
        self.refresh_event = Event()
        self.last_refresh_time = ""

    def run(self):
        """
        运行定时任务，该方法由 start() 自动调用。
        """
        while not self.stop_event.is_set():
            self.perform_update()
            
            # 等待时间间隔或直到收到停止或刷新信号
            self.stop_event.wait(self.interval)
            if self.refresh_event.is_set():
                self.refresh_event.clear()

    def stop(self):
        self.stop_event.set()

    def refresh(self):
        """
        立即刷新数据，而不需要等待下一个间隔。
        """
        self.perform_update()
        self.refresh_event.set()  # 设置刷新事件，以便结束当前的 wait 操作

    def perform_update(self):
        """
        执行数据更新操作。
        """
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tracker is fetching new data...")
        try:
            # 获取新数据
            self.last_refresh_time = time.strftime('%Y-%m-%d %H:%M:%S')
            new_data = self.fetch_data()
            # 更新数据到 DataManager
            changes = self.data_manager.update_questions(new_data)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Data updated. Changes: {changes}")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    from scrapper import ZhihuScraper
    from data import DataManager
    scraper = ZhihuScraper()

    # 假设 data_manager_instance 是已经创建好的 DataManager 实例
    data_manager_instance = DataManager()

    # 创建 DataTracker 实例，并设置每5分钟（300秒）执行一次
    tracker = DataTracker(fetch_data=scraper.fetch_data, data_manager=data_manager_instance, interval=10)

    # 启动定时任务
    tracker.start()

    time.sleep(15)
    # 当需要停止定时任务时，可以调用 stop 方法
    tracker.stop()
    
    scraper.close()
