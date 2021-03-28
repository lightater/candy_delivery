"""
Модуль содержит схемы для валидации данных в запросах и ответах.
Схемы валидации запросов используются в бою для валидации данных отправленных
клиентами.
Схемы валидации ответов *ResponseSchema используются только при тестировании,
чтобы убедиться что обработчики возвращают данные в корректном формате.
"""
from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import DateTime, Dict, Float, Int, List, Nested, Str
from marshmallow.validate import Length, OneOf, Range

from distributor.utils.helpers_func import str_to_time
from distributor.db.schema import TransportType

TIME_HOURS_FORMAT = '%H:%M-%H:%M'


class PatchCourierSchema(Schema):
    courier_type = Str(validate=OneOf(
        [transport.value for transport in TransportType]
    ))
    regions = List(Int(validate=Range(min=0), strict=True))
    working_hours = List(Str(validate=Length(min=11, max=11)))
    earnings = Int(Validate=Range(min=0))

    @validates('regions')
    def validate_regions_unique(self, value: list):
        if len(value) != len(set(value)):
            raise ValidationError('regions must be unique')

    @validates('working_hours')
    def validate_working_hours(self, value: list):
        for val in value:
            try:
                str_to_time(val[:5]), str_to_time(val[6:])
            except ValueError:
                raise ValidationError('working_hours format must be %H%M-%H%M')


class CourierSchema(PatchCourierSchema):
    courier_id = Int(validate=Range(min=0), strict=True, required=True)
    courier_type = Str(validate=OneOf(
        [transport.value for transport in TransportType]
    ), required=True)
    regions = List(Int(validate=Range(min=0), strict=True), required=True)
    working_hours = List(Str(validate=Length(min=1, max=256)), required=True)
    rating = Float(validate=Range(min=0), required=False)
    earnings = Int(validate=Range(min=0), required=False)


class PostCouriersSchema(Schema):
    data = Nested(CourierSchema, many=True, required=True,
                  validate=Length(max=10000))

    @validates_schema
    def validate_unique_courier_id(self, data, **_):
        courier_ids = set()
        for courier in data['data']:
            if courier['courier_id'] in courier_ids:
                raise ValidationError(
                    f'courier_id {courier["courier_id"]} is not unique'
                )
            courier_ids.add(courier['courier_id'])


class PostCouriersIdSchema(Schema):
    courier_id = Int(validate=Range(min=0), strict=True, required=True)


class PostCouriersResponseSchema(Schema):
    couriers28 = Nested(PostCouriersIdSchema(many=True), required=True)


class PatchCourierResponseSchema(Schema):
    data = Nested(CourierSchema(), required=True)


class CourierResponseSchema(Schema):
    data = Nested(CourierSchema(), required=True)


class OrderSchema(Schema):
    order_id = Int(validate=Range(min=0), strict=True, required=True)
    weight = Float(validate=Range(min=0), required=True)
    region = Int(validate=Range(min=0), strict=True, required=True)
    delivery_hours = List(Str(validate=Length(min=11, max=11), strict=True),
                          required=True)

    @validates('delivery_hours')
    def validate_delivery_hours(self, value: list):
        for val in value:
            try:
                str_to_time(val[:5]), str_to_time(val[6:])
            except ValueError:
                raise ValidationError('delivery_hours format must be %H%M-%H%M'
                                      )


class PostOrdersSchema(Schema):
    data = Nested(OrderSchema, many=True, required=True,
                  validate=Length(max=10000))

    @validates_schema
    def validate_unique_courier_id(self, data, **_):
        order_ids = set()
        for order in data['orders']:
            if order['order_id'] in order_ids:
                raise ValidationError(
                    f'order_id {order["order_id"]} is not unique'
                )
            order_ids.add(order['order_id'])


class PostOrdersIdSchema(Schema):
    order_id = Int(validate=Range(min=0), strict=True, required=True)


class PostOrdersResponseSchema(Schema):
    data = Nested(PostOrdersIdSchema(many=True), required=True)


class AssignedOrderSchema(Schema):
    order_id = Int(validate=Range(min=0), strict=True, required=True)
    courier_id = Int(validate=Range(min=0), strict=True, required=True)
    assign_time = DateTime(required=True)


class AssignedOrderResponseSchema(Schema):
    order_ids = List(Int(validate=Range(min=0), strict=True, required=True),
                     required=True)
    assign_time = DateTime(required=False)


class CompletedOrderSchema(Schema):
    order_id = Int(validate=Range(min=0), strict=True, required=True)
    courier_id = Int(validate=Range(min=0), strict=True, required=True)
    complete_time = DateTime(required=True)


class CompletedOrderResponseSchema(Schema):
    order_ids = List(Int(validate=Range(min=0), strict=True, required=True),
                     required=True)
    complete_time = DateTime(required=False)


class ErrorSchema(Schema):
    code = Str(required=True)
    message = Str(required=True)
    fields = Dict()


class ErrorResponseSchema(Schema):
    error = Nested(ErrorSchema(), required=True)
