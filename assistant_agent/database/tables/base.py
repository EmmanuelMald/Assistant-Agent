from abc import ABC, abstractmethod


class Table(ABC):
    @abstractmethod
    def _generate_id(self, **kargs) -> str:
        pass

    @abstractmethod
    def _id_in_table(self, **kargs) -> bool:
        pass

    @abstractmethod
    def _insert_row(self, **kargs) -> str:
        pass

    @abstractmethod
    def generate_new_row(self, **kargs) -> str:
        pass
