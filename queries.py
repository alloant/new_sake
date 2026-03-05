import csv
from app.core.database import get_old_data

notes_in = get_old_data("SELECT note.year, user.alias, count(note.id) as ct FROM note,user WHERE user.id = note.sender_id and user.category = 'ctr' and note.path like '%ctr in%' group by note.year, user.alias")
notes_out = get_old_data("SELECT note.year, user.alias, count(note.id) as ct FROM note,user,noteuser WHERE note.id = noteuser.note_id and user.id = noteuser.user_id and user.category = 'ctr' and note.path like '%ctr out%' group by note.year, user.alias")


with open('flow.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Notes from ctr to cr'])
    writer.writerow(['year','ctr','number'])
    for note in notes_in:
        writer.writerow([note['year'],note['alias'],note['ct']])

    writer.writerow(['Notes from cr to ctr'])
    writer.writerow(['year','ctr','number'])
    for note in notes_out:
        writer.writerow([note['year'],note['alias'],note['ct']])


