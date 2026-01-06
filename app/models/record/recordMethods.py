
class RecordMethod(object):
    @property
    def protocol(self):
        return f'{self.code} {self.sequence}/{str(self.year)[2:]}'

    @property
    def code(self):
        if self.flow.value in self.register.protocol:
            return eval(self.register.protocol[self.flow.value])

        return ''
