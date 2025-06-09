import datetime
from odoo import fields, models, api



class trainingSession(models.Model):
    _name = 'training.session'


    name=fields.Char("Name")
    date=fields.Date(default=datetime.date)
    course_id = fields.Many2one("training.course",string="Course ID")
    instructor_id = fields.Many2one("res.users")
    attendee_ids =fields.Many2one("res.partner")
    available_seats = fields.Integer("Available Seats")
    total_attendees = fields.Integer()
    Seats_taken_percent = fields.Float()