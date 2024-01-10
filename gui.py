import tkinter as tk
from tkinter import ttk
from tracker import DataTracker
from data import DataManager, DataListener
from scrapper import ZhihuScraper

class GUI(DataListener):
    """
    GUI 类用于创建和管理用户界面，以展示问题数据列表，并允许用户与之交互。

    功能细节：
    1. 维护 tracker, scrapper, datamanager 的生命周期，确保它们能按预期工作。
    2. 当 tracker 数据更新时，自动刷新问题数据列表。
    3. 界面上展示问题数据的列表，包括：问题名称、提问时间、潜力值、查看数量与增量、问题数量与增量、是否是关注问题。
       - 关注问题会显示在列表的最前面。
       - 每个问题项旁边有一个按钮来控制是否为关注问题。
       - 列表有滚动条支持。
    4. 显示最近一次刷新问题的时间。

    使用方法:
    创建 GUI 实例并调用 run 方法启动界面。

    示例:
    ```
    gui = GUI(tracker_instance, data_manager_instance)
    gui.run()
    ```

    请注意，本类不包含实际的 tracker 和 datamanager 实现代码，这些需要分别传入实例化对象。
    """

    def __init__(self, interval=10*60):
        """
        初始化 GUI 对象。
        
        :param tracker: DataTracker 实例，负责定时获取新的问题数据。
        :param data_manager: DataManager 实例，负责存储和管理问题数据。
        """
        super().__init__()
        self.scrapper = ZhihuScraper()
        self.data_manager = DataManager()
        self.tracker = DataTracker(self.scrapper.fetch_data, self.data_manager, interval=interval)
        self.data_manager.register_listener(self)
        self.root = tk.Tk()
        self.root.title("Data Tracker GUI")
        
        # 创建问题列表视图
        self.create_list_view()

        # 最后刷新时间标签
        self.last_refresh_label = tk.Label(self.root, text="Last Refresh: N/A")
        self.last_refresh_label.pack()
        
        self.root.bind("<Escape>", self._on_escape_pressed)
        self.root.bind("<F5>", self._force_refresh_data)

        # 启动 tracker
        self.tracker.start()
    
    def create_list_view(self):
        """
        创建问题列表视图。
        """
        self.treeview = ttk.Treeview(
            self.root, columns=("Name", "Time", "Potential", "Views", "View Increment", "Answers", "Answers Increment", "Watched"), show='headings',
            height=40,
            )
        for col in self.treeview['columns']:
            self.treeview.heading(col, text=col)
        self.treeview.pack(fill=tk.BOTH, expand=True)
        column_width = [
            800, 100, 80, 100, 100, 100, 100, 50
        ]
        for i, w in enumerate(column_width):
            self.treeview.column(f"#{i+1}", width=w)
        self.treeview.bind('<Double-1>', self.on_item_checked)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_item_checked(self, event):
        item_id = self.treeview.selection()[0]
        item = self.treeview.item(item_id)
        url = item_id

        # Toggle the checked state
        is_watched = item['values'][-1] == "Yes"
        if is_watched:
            self.data_manager.remove_from_watched(url)
            self.treeview.set(item_id, 'Watched', "No")
        else:
            self.data_manager.add_to_watched(url)
            self.treeview.set(item_id, 'Watched', "Yes")

    def _on_escape_pressed(self, event):
        self.stop()
    
    def _force_refresh_data(self, event):
        self.tracker.refresh()

    def refresh_list(self):
        """
        刷新问题列表。
        """
        # 获取最新问题数据
        watched_questions = self.data_manager.watched_questions

        # 清空当前列表
        for i in self.treeview.get_children():
            self.treeview.delete(i)
        
        self.question_list = self.data_manager.get_question_list()

        for question in self.question_list:
            values = (
                question['question_text'], 
                question['date'], 
                question['potential_score'], 
                question['view_total'], 
                question['view_increment'], 
                question['answer_total'], 
                question['answer_increment'], 
                "Yes" if question['question_url'] in watched_questions else "No"
            )
            self.treeview.insert('', 'end', values=values, iid=question['question_url'])

        # 更新最后刷新时间
        self.last_refresh_label.config(text=f"Last Refresh: {self.tracker.last_refresh_time}")

    def run(self):
        """
        运行 GUI 应用程序。
        """
        self.refresh_list()
        self.root.mainloop()
    
    def stop(self):
        """
        停止 GUI 应用程序和相关的 tracker。
        """
        self.tracker.stop()
        self.scrapper.close()
        self.root.destroy()
        
    def update(self, data):
        self.refresh_list()

if __name__ == "__main__":
    # 假设 tracker_instance 是 DataTracker 类的实例化对象
    # 假设 data_manager_instance 是 DataManager 类的实例化对象
    gui = GUI()
    gui.run()
