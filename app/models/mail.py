from pathlib import Path
import sqlalchemy as sa
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

def get_class_icon(name):
    match Path(name).suffix:
        case '.xls' | '.xlsx':
            return 'primary','file-excel'
        case '.doc' | '.docx':
            return 'link','file-word'
        case '.ppt' | '.pptx':
            return 'warning','file-powerpoint'
        case '.pdf':
            return 'danger','file-pdf'
        case '': # Folder
            return '',''
        case '.mp4' | '.mkv':
            return 'info','file-video'
        case '.mp3' | '.wav':
            return 'info', 'file-music'
        case '.jpg' | '.gif' | '.png':
            return 'warning','file-image'
        case _:
            return 'secondary','file-document-online'

class Mail(SQLModel, table=True):
    id: int | None = Field(default = None, primary_key = True)
    uid: str = Field(unique=True, max_length = 10)
    from_: str = Field(max_length = 100)
    subject: str = Field(max_length = 500, default = None)
    text: str = Field(max_length = 500, default = None)
    date: datetime = Field()
    downloaded: bool = Field(default = False)

    created_at: datetime | None = Field(default_factory=datetime.utcnow)

    attachments: list["Attachment"] = Relationship()


class Attachment(SQLModel, table=True):
    id: int | None = Field(default = None, primary_key = True)
    uid: str = Field(max_length = 10, foreign_key="mail.uid")
    name: str = Field(max_length = 100)
    content_type: str = Field(max_length = 200)
    file_data: bytes = Field(sa_type=sa.LargeBinary)

    created_at: datetime | None = Field(default_factory=datetime.utcnow)

    @property
    def icon(self):
        rst = get_class_icon(self.name)
        if not self.file_data:
            rst = 'grey', rst[1]

        return rst

    @property
    def html_icon(self):
        rst = f"""
            <span class="icon" title="{self.name}">
                <span class="iconify has-text-{self.icon[0]}" data-width="1em" data-icon="mdi-{self.icon[1]}"></span>
            </span>
              """
        return rst

