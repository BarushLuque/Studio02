from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from DAO.db import Base


class CategoriaServicio(Base):
    __tablename__ = 'categorias_servicio'

    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre_categoria = Column(String(100), nullable=False)

    # Relación: una categoría tiene muchos servicios
    servicios = relationship("Servicio", back_populates="categoria")
