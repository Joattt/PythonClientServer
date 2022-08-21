class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            raise ValueError(f'Некорректный номер порта: {value}!')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
