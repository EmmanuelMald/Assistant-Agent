from abc import ABC, abstractmethod


class Table(ABC):
    @abstractmethod
    def _generate_id():
        pass

    @abstractmethod
    def _id_in_table():
        pass

    @abstractmethod
    def _insert_row():
        pass

    @abstractmethod
    def generate_new_row():
        pass
