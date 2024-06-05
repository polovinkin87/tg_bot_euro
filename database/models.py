from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, BigInteger, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Group(Base):
    __tablename__ = 'group'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class Game(Base):
    __tablename__ = 'game'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner: Mapped[str] = mapped_column(String(50), nullable=False)
    guest: Mapped[str] = mapped_column(String(50), nullable=False)
    goals_owner: Mapped[int] = mapped_column(Numeric, nullable=True)
    goals_guest: Mapped[int] = mapped_column(Numeric, nullable=True)
    date_time: Mapped[DateTime] = mapped_column(DateTime)
    group_id: Mapped[int] = mapped_column(ForeignKey('group.id', ondelete='CASCADE'), nullable=False)

    group: Mapped['Group'] = relationship(backref='game')
    # forecasts: Mapped['Forecast'] = relationship(backref='game')


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True)


class Forecast(Base):
    __tablename__ = 'forecast'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    owner: Mapped[int]
    guest: Mapped[int]

    user: Mapped['User'] = relationship(backref='forecast')
    game: Mapped['Game'] = relationship(backref='forecast')
