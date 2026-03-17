import unittest

class TestTaskQueueSingleton(unittest.TestCase):

    def test_get_task_queue_singleton(self):
        from core.task_queue import get_task_queue

        queue1 = get_task_queue()
        queue2 = get_task_queue()

        self.assertIs(queue1, queue2, "get_task_queue() should return the exact same instance")

if __name__ == '__main__':
    unittest.main()
