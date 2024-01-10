import json
import os
from datetime import datetime


class DataListener:
    """
    DataListener 是一个监听者基类，其子类需要实现 update 方法以接收数据更新的通知。
    """
    def update(self, data):
        """
        当数据更新时调用此方法。

        :param data: 更新的数据。
        """
        raise NotImplementedError("Subclasses must implement this method to receive data updates.")


class EventSource:
    """
    EventSource 类用于跟踪数据，并在数据更新时通知所有注册的监听者。
    """
    def __init__(self):
        self._data = None
        self._listeners = []

    @property
    def data(self):
        """获取当前数据"""
        return self._data

    @data.setter
    def data(self, value):
        """
        设置新的数据并通知所有监听者。
        
        :param value: 新的数据值。
        """
        self._data = value
        self._notify_listeners()
    
    def register_listener(self, listener):
        """
        注册一个新的监听者。
        
        :param listener: 实现了 DataListener 接口的监听者对象。
        """
        if isinstance(listener, DataListener) and listener not in self._listeners:
            self._listeners.append(listener)
        else:
            raise TypeError("The listener must be an instance of DataListener")

    def unregister_listener(self, listener):
        """
        取消注册一个监听者。
        
        :param listener: 需要取消注册的监听者对象。
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self):
        """通知所有已注册的监听者数据更新。"""
        for listener in self._listeners:
            listener.update(self._data)
        

class DataManager(EventSource):
    """
    数据管理系统，负责处理从scrapper下载的问题数据。
    
    功能包括：
    1. 保存下载下来的问题数据，以question_url作为唯一标识，并记录保存时间。
    2. 对比新旧问题数据，得到数据变化情况和新出现的问题项。
    3. 维护一个关注问题列表，并允许添加或删除问题。
    """

    def __init__(self, data_file='questions.json', watched_file='watched_questions.json', max_history=3):
        super().__init__()
        self.data_file = data_file
        self.watched_file = watched_file
        self.max_history = max_history  # 最多保存的历史数据数量
        self.questions = self.load_data(self.data_file)
        self.watched_questions = self.load_data(self.watched_file)

    def get_question_list(self):
        """
        获取问题列表。

        :return: 问题列表
        """
        question_list = []
        question_id_list = []
        for watch in self.watched_questions:
            question_items = self.questions.get(watch, [])
            if len(question_items) > 0:
                question_list.append(question_items[-1])
                question_id_list.append(watch)
        
        raw_questions_list = sorted(self.questions.items(), key=lambda x: x[1][0]["potential_score"], reverse=True)
        for key, question_items in raw_questions_list:
            if len(question_items) == 0:
                continue
            if key not in question_id_list:
                question_list.append(question_items[-1])
                question_id_list.append(key)
        return question_list

    def load_data(self, file_path):
        """
        加载数据文件。

        :param file_path: 数据文件路径
        :return: 数据字典
        """
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}

    def save_data(self, data, file_path):
        """
        保存数据到文件中。

        :param data: 要保存的数据
        :param file_path: 数据文件路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def update_question_history(self, question_url, new_data):
        """
        更新问题的历史数据。

        :param question_url: 问题的URL标识
        :param new_data: 新的问题数据
        """
        if question_url not in self.questions:
            self.questions[question_url] = []

        history = self.questions[question_url]
        # 记录保存的时间
        new_data['saved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append(new_data)

        # 如果历史数据超过最大数量，移除最旧的数据
        while len(history) > self.max_history:
            history.pop(0)

    def update_questions(self, new_questions):
        """
        更新问题数据。

        :param new_questions: 新下载的问题数据列表
        :return: 变化情况和新出现的问题
        """
        changes = {'updated': [], 'new': []}
        
        for question in new_questions:
            question_url = question['question_url']
            if question_url in self.questions and self.questions[question_url]:
                old_data = self.questions[question_url][-1]  # 获取最后一条历史记录
                view_increment = question['view_total'] - old_data['view_total']
                answer_increment = question['answer_total'] - old_data['answer_total']
                
                # 只有在增量不为零时才认为是更新
                if view_increment or answer_increment:
                    changes['updated'].append({
                        'question_url': question_url,
                        'view_increment': view_increment,
                        'answer_increment': answer_increment
                    })
            else:
                changes['new'].append(question)
            
            # 更新问题的历史数据
            self.update_question_history(question_url, question)
        
        # 保存更新后的数据
        self.save_data(self.questions, self.data_file)
        
        self._notify_listeners()
        return changes

    def add_to_watched(self, question_url):
        """
        添加问题到关注列表。

        :param question_url: 问题的URL
        """
        if question_url not in self.watched_questions and question_url in self.questions:
            # 添加最近的数据到关注列表
            self.watched_questions[question_url] = self.questions[question_url][-1]
            self.save_data(self.watched_questions, self.watched_file)

    def remove_from_watched(self, question_url):
        """
        从关注列表移除问题。

        :param question_url: 问题的URL
        """
        if question_url in self.watched_questions:
            del self.watched_questions[question_url]
            self.save_data(self.watched_questions, self.watched_file)

if __name__ == "__main__":
    # 使用示例
    data_manager = DataManager()

    # # 假设这是新获取的问题数据
    # new_questions = [
    #     {
    #         "question_text": "鲁东大学一学生疑被冰锥砸中倒地，医院工作人员称「已去世」，具体情况如何？责任该如何判定？",
    #         "question_url": "https://www.zhihu.com/question/638355600",
    #         "topics": ["#医院", "#安全", "#鲁东大学"],
    #         "date_raw": "提问时间：2024-01-06",
    #         "potential_score_raw": "7.1 分",
    #         "view_amount_raw": "2.4 万\n共 142 万",
    #         "answer_amount_raw": "3\n共 148",
    #         "potential_score": 7.1,
    #         "view_increment": 24000.0,
    #         "view_total": 1420000.0,
    #         "answer_increment": 3,
    #         "answer_total": 148,
    #         "date": "2024-01-06"
    #     },
    #     # 更多问题数据...
    # ]
    with open("potential_data.json", "r", encoding="utf-8") as f:
        new_questions = json.load(f)
    # 更新问题数据并获取变化情况
    changes = data_manager.update_questions(new_questions)
    print(changes)

    # 将问题添加到关注列表
    data_manager.add_to_watched("https://www.zhihu.com/question/638671506")

    # # 从关注列表移除问题
    # data_manager.remove_from_watched("https://www.zhihu.com/question/638355600")
