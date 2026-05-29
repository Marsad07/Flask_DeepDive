from app2.database import db

class BaseModel(db.Model):
    """
    Abstract base model — every ORM model inherits from this.
    Provides get_by_id, find, first, save, delete so controllers
    never write raw SQL directly.
    """
    __abstract__ = True  # This prevents SQLAlchemy from creating a table for this class

    @classmethod
    def get_by_id(cls, id):
        """Return a single row by primary key, or None."""
        return cls.query.get(id)

    @classmethod
    def find(cls, **kwargs):
        """Return all rows matching keyword filters. e.g. Order.find(order_status='pending')"""
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def first(cls, **kwargs):
        """Return first row matching keyword filters, or None."""
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def all(cls):
        """Return every row in the table."""
        return cls.query.all()

    def save(self):
        """INSERT or UPDATE this instance to the DB and commit."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """DELETE this instance from the DB and commit."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def create(cls, **kwargs):
        """Convenience method — instantiate, save, and return."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, **kwargs):
        """Update multiple fields at once and commit."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def to_dict(self):
        """Serialise model to a plain dict — useful for JSON responses."""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }