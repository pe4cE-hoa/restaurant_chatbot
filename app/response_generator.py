"""
Developed by HH
"""

import json
import random
import datetime
import pymongo
import uuid
import re

from bson import json_util

import intent_classifier


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["restaurant"]
menu_collection = db["menu"]
feedback_collection = db["feedback"]
bookings_collection = db["bookings"]
table_manager = client["table_manager"]
seat_count = 3 # chỉ số test
seat_count_available = 0

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

def check_date_booking(date):
    """
    date yyyy-mm-dd
    """
    now = datetime.datetime.now()
    today = now.date()
    string_date = str(date)
    datecheck = datetime.date(*[int(i) for i in string_date.split("-")])
    if today == datecheck:
        return "today"
    elif today < datecheck: 
        return "future"
    else:
        return "past"

def book_table_list_available(date, time1, time2):
    """   
    date yyyy-mm-dd
    """
    #query theo timenow -> available time nhap vao lon hon time hien tai
    global seat_count_available
    seat_count_available = 0
    table_list_available = []
    for i in range(seat_count):
        table_number = "table" + str(i + 1)
        table_number_i = table_manager[table_number]
        query = {"date": date, 
                "$or" : 
                    [{"time1":{"$gte":time2}},
                     {"time2":{"$lte":time1}}]}
        table_doc = table_number_i.count_documents(query)
        if table_doc == table_number_i.count_documents({"date": date}):
            table_list_available.append(i + 1)
            seat_count_available += 1
    return table_list_available
        
        
def available_tables_now():
    now = datetime.datetime.now()
    date = now.date()
    hour = now.hour
    table_list_available = book_table_list_available(date, hour, hour)
    if seat_count_available > 0:
        response = "Đang có " + str(seat_count_available) + " bàn sẵn sàng trong lúc này.\nCác bàn đó là: "
        for i in table_list_available:
            response += str(i) + ", "
    else:
        response = "Xin lỗi quý khách hiện tại nhà hàng đã hết bàn!"
    return response

def book_table(*arg):
    success = False
    table_list_available = book_table_list_available(*arg)
    response = ""
    now = datetime.datetime.now()
    date = now.date()
    hour_now = now.hour - 1
    date_check = datetime.date(*[int(i) for i in arg[0].split("-")])
    if date_check < date:
        response = 'Bạn đang đặt khung giờ trong quá khứ ư! <(")'
        response += "\n Vui lòng nhập thời điểm đặt bàn theo định dạng(năm/tháng/ngày giờ_đăt giờ_trả)(vd:2023-6-18 19 21)"
    elif int(arg[2]) < hour_now and date_check == date:
        response = 'Bạn đang đặt khung giờ trong đã qua trong ngày hôm nay ư! <(")'
        response += "\n Vui lòng nhập thời điểm đặt bàn theo định dạng(năm/tháng/ngày giờ_đăt giờ_trả)(vd:2023-6-18 19 21)"
    else:
        if seat_count_available > 0:
            response = "Bàn của bạn đã được đặt thành công." 
            response += "\n Số bàn:" + str(table_list_available[0])
            response += "\n Thời điểm đặt bàn: " + date_check.strftime('%Y-%m-%d')      
            response += " Khung giờ từ " +str(arg[1]) + "h đến " +str(arg[2]) + "h"       
            booking_doc = code_booking()
            response += "\n Mã ID bàn của bạn: " + booking_doc["booking_id"]
            success = True
            #lưu vào mongodb
            table_number = "table" + str(table_list_available[0])
            table_number_i = table_manager[table_number]
            table_doc = {"date":arg[0], "time1": arg[1], "time2": arg[2]}
            table_number_i.insert_one(table_doc)
            #relationship table and booking
            table_doc_id = json_util.dumps(table_number_i.find({"date":arg[0], "time1": arg[1], "time2": arg[2]}
                                                               ,{"_id": 1, "date": 0, "time1": 0 , "time2":0}))
            
            booking_doc["table_id"] = str(table_doc_id)
            bookings_collection.insert_one(booking_doc)
            
        else:
            response = "Xin lỗi thời gian quý khách chọn đã được đặt!"
            response += "\n Vui lòng nhập thời điểm đặt bàn theo định dạng(năm/tháng/ngày giờ_đăt giờ_trả)(vd:2023-6/18 19 21)"
    return response, success 
        
        
def code_booking():
    booking_id = str(uuid.uuid4())
    now = datetime.datetime.now()
    booking_time = now.strftime("%Y-%m-%d %H:%M:%S")
    booking_doc = {"booking_id": booking_id, "booking_time": booking_time}
    return booking_doc          


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


insert_date_book = False
booking = False

def generate_response(message):
    tag = "book_table" 
    global seat_count_available,insert_date_book, booking
    if not booking:
        tag = get_intent(message)
    response = ""
    if insert_date_book:
        #message: yyyy-mm-dd t1 t2
        x = re.split('\s', message)
        date = x[0]
        time1 = x[1]
        time2 = x[2]
        tag = "book_table"
        try:
            if not (0 <= int(time1) < int(time2) <= 24):
                raise ValueError
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            response = 'Bạn đang nhập sai đinh dạng ngày tháng <(").'
            response += "\n Vui lòng nhập thời điểm đặt bàn theo định dạng(năm/tháng/ngày giờ_đăt giờ_trả)(vd:2023-6-18 19 21)"
            return response
 
    if tag != "":
        if tag == "book_table":
            booking = True
            if not insert_date_book:
                response = "Vui lòng nhập thời điểm đặt bàn theo định dạng(năm-tháng-ngày giờ_đăt giờ_trả)(vd:2023-6-18 19 21)"
                insert_date_book = True
                return response
            
            success = False
            check_date = check_date_booking(date)
            if check_date ==  "today":
                response, success = book_table(date, time1, time2)
                if success:
                    response += "\n Chúc bạn dùng bữa ngon miệng. Thanks ^^"
                    booking = False
                    insert_date_book = False
                
            elif check_date == "future": 
                response, success = book_table(date, time1, time2)
                if success:
                    response += "\n Hãy lưu lại mã ID để xuất trình ID tại quầy vào ngày đặt bàn. Thanks ^^"
                    booking = False
                    insert_date_book = False
                
            else:
                response += '\n Chúng tôi không thể phục vụ thời gian ở quá khứ <(").'
                response += "\n Vui lòng nhập thời điểm đặt bàn theo định dạng(năm/tháng/ngày giờ_đăt giờ_trả)(vd:2023-6-18 19 21)"

        elif tag == "available_tables":
            response = available_tables_now()

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
