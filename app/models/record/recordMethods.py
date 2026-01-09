from datetime import date
from app.views.actions import get_actions

class RecordMethod(object):
    @property
    def protocol(self):
        return f'{self.code} {self.sequence}/{str(self.year)[2:]}'

    @property
    def code(self):
        if self.flow.value in self.register.protocol:
            return eval(self.register.protocol[self.flow.value])

        return ''

    @property
    def date(self):
        return self.updated_at.strftime('%Y-%m-%d') if self.updated_at > self.created_at else self.created_at.strftime('%Y-%m-%d')

    def get_actions(self, user_perms, section: str, panel: str):
        return get_actions(user_perms, section, panel)
