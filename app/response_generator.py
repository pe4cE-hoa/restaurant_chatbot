"""
Developed by Nhom2 in November, 2021
"""

import json
import random
import datetime
import pymongo
import uuid

import intent_classifier

seat_count = 50
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["restaurant"]
menu_collection = db["menu"]
feedback_collection = db["feedback"]
bookings_collection = db["bookings"]
with open("data\dataset.json", encoding='utf-8') as file:
    data = json.load(file)


def get_intent(message):
    tag = intent_classifier.classify(message)
    return tag

'''
Reduce seat_count variable by 1
Generate and give customer a unique booking ID if seats available
Write the booking_id and time of booking into Collection named bookings in restaurant database
'''
def book_table():
    global seat_count
    seat_count = seat_count - 1
    booking_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    booking_time = now.strftime("%Y-%m-%d %H:%M:%S")
    booking_doc = {"booking_id": booking_id, "booking_time": booking_time}
    bookings_collection.insert_one(booking_doc)
    return booking_id


def vegan_menu():
    query = {"vegan": "Y"}
    vegan_doc = menu_collection.find(query)
    if vegan_doc.count() > 0:
        response = "thực đơn cho người thuần ăn chay gồm: "
        for x in vegan_doc:
            response = response + str(x.get("item")) + " với Rs. " + str(x.get("cost")) + "; "
        response = response[:-2] # to remove the last ;
    else:
        response = "Xin lỗi hiện tại nhà hàng không phục vụ đồ ăn thuần chay"
    return response


def veg_menu():
    query = {"veg": "Y"}
    vegan_doc = menu_collection.find(query)
    if vegan_doc.count() > 0:
        response = "thực đơn cho người ăn chay gồm: "
        for x in vegan_doc:
            response = response + str(x.get("item")) + " với Rs. " + str(x.get("cost")) + "; "
        response = response[:-2] # to remove the last ;
    else:
        response = "Xin lỗi hiện tại nhà hàng không phục vụ đồ ăn chay"
    return response


def offers():
    all_offers = menu_collection.distinct('offer')
    if len(all_offers)>0:
        response = "ưu đãi đặc biệt gồm: "
        for ofr in all_offers:
            docs = menu_collection.find({"offer": ofr})
            response = response + ' ' + ofr.upper() + " On: "
            for x in docs:
                response = response + str(x.get("item")) + " - Rs. " + str(x.get("cost")) + "; "
            response = response[:-2] # to remove the last ;
    else:
        response = "Xin lỗi hiện tại không có ưu đãi đặc biệt nào."
    return response


def suggest():
    day = datetime.datetime.now()
    day = day.strftime("%A")
    if day == "Monday":
        response = "Chef recommends: Paneer Grilled Roll, Jade Chicken"
    elif day == "Tuesday":
        response = "Chef recommends: Tofu Cutlet, Chicken A La King"

    elif day == "Wednesday":
        response = "Chef recommends: Mexican Stuffed Bhetki Fish, Crispy corn"

    elif day == "Thursday":
        response = "Chef recommends: Mushroom Pepper Skewers, Chicken cheese balls"

    elif day == "Friday":
        response = "Chef recommends: Veggie Steak, White Sauce Veggie Extravaganza"

    elif day == "Saturday":
        response = "Chef recommends: Tofu Cutlet, Veggie Steak"

    elif day == "Sunday":
        response = "Chef recommends: Chicken Cheese Balls, Butter Garlic Jumbo Prawn"
    return response


def recipe_enquiry(message):
    all_foods = menu_collection.distinct('item')
    response = ""
    for food in all_foods:
        query = {"item": food}
        food_doc = menu_collection.find(query)[0]
        if food.lower() in message.lower():
            response = food_doc.get("about")
            break
    if "" == response:
        response = "Xin lỗi vui lòng quý khách viết chính xác lại mặt hàng sản phẩm!"
    return response


def record_feedback(message, type):
    feedback_doc = {"feedback_string": message, "type": type}
    feedback_collection.insert_one(feedback_doc)


def get_specific_response(tag):
    for intent in data['intents']:
        if intent['tag'] == tag:
            responses = intent['responses']
    response = random.choice(responses)
    return response


def show_menu():
    all_items = menu_collection.distinct('item')
    response = ', '.join(all_items)
    return response


def generate_response(message):
    global seat_count
    tag = get_intent(message)
    response = ""
    if tag != "":
        if tag == "book_table":

            if seat_count > 0:
                booking_id = book_table()
                response = "Bàn của bạn đã được đặt thành công. Vui lòng xuất trình ID đặt chỗ này tại quầy:" + str(
                    booking_id)
            else:
                response = "Xin lỗi quý khách hiện tại nhà hàng đã hết bàn!"


        elif tag == "available_tables":
            response = "There are " + str(seat_count) + " table(s) available at the moment."

        elif tag == "veg_enquiry":
            response = veg_menu()

        elif tag == "vegan_enquiry":
            response = vegan_menu()

        elif tag == "offers":
            response = offers()

        elif tag == "suggest":
            response = suggest()

        elif tag == "recipe_enquiry":
            response = recipe_enquiry(message)

        elif tag == "menu":
            response = show_menu()

        elif tag == "positive_feedback":
            record_feedback(message, "positive")
            response = "Cảm ơn quý khách đã để lại phản hồi cho nhà hàng của chúng tôi. Chúng tôi rất mong lại được phục vụ bạn trong thời gian ngắn tới!"

        elif "negative_feedback" == tag:
            record_feedback(message, "negative")
            response = "Cảm ơn quý khách đã để lại phản hồi cho nhà hàng của chúng tôi. Chúng tôi rất lấy lòng tiếc vì sự bất tiện này. Chúng tôi sẽ " \
                       "gửi phản hồi của bạn lên quản lý và mong rằng sẽ được phục vụ bạn tốt hơn vào lần tới ! "
        # for other intents with pre-defined responses that can be pulled from dataset
        else:
            response = get_specific_response(tag)
    else:
        response = "Xin lỗi! tôi chưa hiểu ý bạn, bạn có thể nói rõ hơn cho tôi được không.(^^)"
    return response
