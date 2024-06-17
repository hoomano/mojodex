from abc import ABCMeta
from sqlalchemy.ext.declarative import DeclarativeMeta

# Create a custom metaclass that inherits from both ABCMeta and DeclarativeMeta
class AbstractEntity(DeclarativeMeta, ABCMeta):
    pass