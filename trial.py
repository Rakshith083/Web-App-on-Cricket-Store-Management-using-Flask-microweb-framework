from flask import *
from cacon import cassandra_connect
import re
import random
from datetime import datetime, timedelta, date
from flask_mail import *
from random import *

app = Flask(__name__)
app.secret_key = "rakshi"
order = []
quantity = 0
a = ['Product Id', 'Product ', 'Brand', 'Model', 'Weight', 'Price', 'Stocks']
l = ['Product ', 'Brand', 'Model', 'Weight', 'Price', 'Stocks']
custord = ["Order Id", "Product ID", "Product", "Brand",
           "Model", "Price", "Ordered Date", "Delivery Date"]
account = []
m = []

mail = Mail(app)

app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'rcbbrandcollection@gmail.com'
app.config['MAIL_PASSWORD'] = 'eesalacupnamde'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
otp = randint(000000, 999999)
print(otp)


@app.route('/Userauth')
def index():
    return render_template("otpindex.html")


@app.route('/verify', methods=["POST"])
def verify():
    email = request.form["mail"]
    name = request.form["name"]
    phone = int(request.form["phone"])

    msg = Message('OTP', sender='rcbbrandcollection@gmail.com',
                  recipients=[email])
    msg.body = str(otp)
    mail.send(msg)
    return render_template('verify.html', name=name, mail=email, phone=phone)


confirmmsg = "Your account created successfully on RCB BRAND COLLECTION,Now you can shop more cricket lits on RCB BRAND COLLECTION "


@app.route('/validate', methods=["POST"])
def validate():
    user_otp = request.form['otp']
    if otp == int(user_otp):
        name = request.form['name']
        phone = int(request.form['phone'])
        email = request.form['mail']
        pas = request.form['pas']
        add = request.form['address']

        csession = cassandra_connect()
        csession.execute('USE trial')
        csession.execute(
            """
            INSERT INTO customer(name,phone,mail,pwd,address)
            VALUES (%(name)s, %(phone)s,%(mail)s,%(pwd)s,%(address)s)
            """, {'name': name, "phone": phone, "mail": email, 'pwd': pas, 'address': add},
        )
        msg = Message(
            'Confirmation', sender='rcbbrandcollection@gmail.com', recipients=[email])
        msg.body = confirmmsg
        mail.send(msg)
        return render_template("msg.html", msg=" Account created", m=email)
    else:
        return "<h3>failure</h3>"


@app.route('/menu')
def menu():
    return render_template("menu.html")


@app.route('/', methods=['GET', 'POST'])
def log():
    if request.method == "GET":
        return render_template("newlogin.html")
    else:
        mail = request.form['mail']
        pas = request.form['pas']

        csession = cassandra_connect()
        csession.execute('USE trial')
        rows = csession.execute('select * from customer where mail=%(mail)s and pwd=%(pwd)s ALLOW FILTERING',
                                {'mail': mail, 'pwd': pas})
        r = []
        for c_row in rows:
            r.append([c_row.mail, c_row.pwd])
            if c_row.mail == mail and c_row.pwd == pas:
                account.append(c_row.mail)
                account.append(c_row.name)
                account.append(c_row.phone)
                account.append(c_row.pwd)
                account.append(c_row.address)
                print(account)
                session['email'] = account[0]
                return render_template("products.html", m=mail, acc=account[0])

        # r=tuple(r)
        print(r)


@app.route('/logout', methods=['GET'])
def logout():
    account.clear()
    print(account)
    print("Cleared")
    if 'email' in session:
        session.pop('email', None)
        return render_template("msg.html", msg="Logged out")
    else:
        return render_template("msg.html", msg="User Already Logged out")


@app.route('/<item>')
def show_item(item):
    return render_template("brands.html", acc=account[0], item=item)


@app.route('/profileupdate/<email>', methods=['GET'])
def profileupdate(email):
    mail = email
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from customer where mail=%(mail)s',
                            {'mail': mail})
    r = []
    for cst_row in rows:
        r.append([cst_row.name, cst_row.phone, cst_row.address, cst_row.pwd])
    r = tuple(r)
    c = []
    for row in r:
        for col in row:
            c.append(col)
            print(col)
    return render_template("profileupdate.html", mail=mail, name=c[0], phone=c[1], address=c[2], pwd=c[3])


@app.route('/profileupdate', methods=['POST'])
def profileupdatepost():
    mail = request.form['mail']
    name = request.form['name']
    phone = int(request.form['phone'])
    pwd = request.form['pwd']
    address = request.form['address']

    csession = cassandra_connect()
    csession.execute('USE trial')

    csession.execute(
        """
    UPDATE customer set name=%(name)s,phone=%(phone)s
    ,pwd=%(pwd)s,address=%(address)s where mail=%(mail)s
    """,
        {'mail': mail, 'name': name, 'phone': phone, 'pwd': pwd, 'address': address}
    )
    return render_template("msg.html", msg="Account updated,pls login again", m=mail)


@app.route('/products')
def products():
    return render_template("products.html", acc=account[0])


@app.route('/add', methods=['GET', 'POST'])
def add2():
    if request.method == "GET":
        sn = randint(1, 9999999999)
        return render_template("add.html", sn=sn)
    else:
        serial = int(request.form['serial'])
        brand = request.form['brand']
        model = request.form['model']
        stocks = int(request.form['stocks'])
        weight = request.form['weight']
        price = request.form['price']
        product = request.form['product']

        csession = cassandra_connect()
        csession.execute('USE trial')
        csession.execute(
            """
        INSERT INTO products (serialno,brand,modelname,stocks,weight,price,producttype)
        VALUES (%(serialno)s, %(brand)s, %(modelname)s, %(stocks)s,%(weight)s,%(price)s,%(producttype)s)
        """, {'serialno': serial, 'brand': brand, 'modelname': model, "stocks": stocks, "weight": weight, 'price': price, 'producttype': product},
        )
        return "insereted"


@app.route('/update/<int:i>/', methods=['GET'])
def update(i):
    sn = i
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from products where serialno=%(serialno)s',
                            {'serialno': i})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.producttype, pdt_row.brand, pdt_row.modelname,
                 pdt_row.weight, pdt_row.price, pdt_row.stocks])
    r = tuple(r)
    # pt,br,mdl,prc,wt,st
    c = []
    for row in r:
        for col in row:
            c.append(col)
            print(col)
    return render_template("showall2.html", sn=i, pt=c[0], br=c[1], mdl=c[2], prc=c[4], wt=c[3], st=c[5])


@app.route('/update', methods=['POST'])
def updatepost():
    serial = int(request.form['serial'])
    brand = request.form['brand']
    model = request.form['model']
    stocks = int(request.form['stocks'])
    weight = request.form['weight']
    price = request.form['price']
    product = request.form['product']

    csession = cassandra_connect()
    csession.execute('USE trial')

    csession.execute(
        """
    UPDATE products set brand=%(brand)s,modelname =%(modelname)s
    ,weight=%(weight)s,price=%(price)s,producttype=%(producttype)s,stocks=%(stocks)s where serialno=%(serialno)s
    """,
        {'serialno': serial, 'brand': brand, 'modelname': model, 'weight': weight,
            'price': price, 'producttype': product, 'stocks': stocks}
    )
    return "<h2>Updated</h2>"


@app.route('/productdelete/<int:serialno>', methods=['GET', 'POST'])
def delete(serialno):
    serial = serialno

    csession = cassandra_connect()
    csession.execute('USE trial')
    csession.execute(
        """
        DELETE from products where serialno=%(serialno)s
        """,
        {'serialno': serial})
    return "<h2>Product Deleted...</h2>"


@app.route('/show', methods=['GET'])
def showall():
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from products')
    r = []
    for pdt_row in rows:
        r.append([pdt_row.serialno, pdt_row.producttype, pdt_row.brand,
                 pdt_row.modelname, pdt_row.weight, pdt_row.price, pdt_row.stocks])
    r = tuple(r)
    print(r)
    return render_template('showall.html', r=r, a=a, zip=zip)


@app.route('/Appholder/<item>')
def show_item_to_holder(item):
    producttype = item
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from products where producttype=%(producttype)s ALLOW FILTERING',
                            {'producttype': producttype})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.serialno, pdt_row.producttype, pdt_row.brand,
                 pdt_row.modelname, pdt_row.weight, pdt_row.price, pdt_row.stocks])
    r = tuple(r)
    print()
    # return render_template('item_show.html',r=r,l=l,zip=zip,acc=account[0])
    return render_template('showall.html', r=r, a=a, zip=zip)


@app.route('/show/<item>/<name>', methods=['GET'])
def display(item, name):
    producttype = item
    brand = name
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from products where producttype=%(producttype)s and brand=%(brand)s ALLOW FILTERING',
                            {'brand': brand, 'producttype': item})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.producttype, pdt_row.brand, pdt_row.modelname,
                 pdt_row.weight, pdt_row.price, pdt_row.stocks])
    # r=tuple(r)
    print(r)
    r1 = r[0][0]
    # return render_template('disp.html',r=r,l=a,zip=zip)
    return render_template('disp.html', r=r, r1=r1, l=l, zip=zip, acc=account[0])


@app.route('/show/<item>/<name>/<model>')
def display2(item, name, model):
    producttype = item
    brand = name
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from products where producttype=%(producttype)s and brand=%(brand)s and modelname=%(modelname)s ALLOW FILTERING',
                            {'producttype': item, 'brand': brand, 'modelname': model})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.serialno, pdt_row.producttype, pdt_row.brand,
                 pdt_row.modelname, pdt_row.weight, pdt_row.price, pdt_row.stocks])
    order.append(r[0][0])
    print(order)
    r = tuple(r)
    print(r)
    return render_template('specific_item_show.html', r=r, a=a, zip=zip, acc=account[0])


@app.route('/order/new', methods=['post'])
def ordproduct():
    sn = order[-1]
    quantity = request.form['quantity']
    csession = cassandra_connect()
    csession.execute('USE trial')
    print("quantity=", quantity)
    od = randint(0, 999999999)
    ordid = "ORD"+str(od)
    print(ordid)

    orddate = date.today().strftime("%b-%d-%Y")
    print(orddate)

    deldate = (date.today()+timedelta(randint(1, 6))).strftime("%b-%d-%Y")
    print(deldate)

    rows = csession.execute('select * from products where serialno=%(serialno)s',
                            {'serialno': sn})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.producttype, pdt_row.brand,
                 pdt_row.modelname, pdt_row.price, pdt_row.serialno])
    r = tuple(r)
    # pt,br,mdl,prc,wt,st
    c = []
    for row in r:
        for col in row:
            c.append(col)
            print(col)
    print(c)

    s21 = re.findall(r'\d+', c[3])
    print("Price = ", int(s21[0]))
    mi = int(s21[0])
    tc = (mi*int(quantity))
    return render_template("order.html", q=quantity, pt=c[0], br=c[1], mdl=c[2], prc=tc, sn=c[4], oid=ordid, orddate=orddate, deldate=deldate, name=account[1], mail=account[0], phone=account[2], add=account[4])


@app.route('/order', methods=['POST'])
def ordrecieve():
    name = request.form['name']
    phone = int(request.form['phone'])
    email = request.form['mail']
    add = request.form['address']

    oid = request.form['oid']

    serial = request.form['serial']
    brand = request.form['brand']
    model = request.form['model']
    product = request.form['product']
    price = request.form['price']+"/- Rs"

    odate = request.form['odate']
    ddate = request.form['ddate']

    csession = cassandra_connect()
    csession.execute('USE trial')

    csession.execute(
        """
        INSERT INTO orders (orderid , address , brand , customername , deleverydate , email , modelname , orddate , phone , price , producttype,serialno)
        VALUES (%(orderid)s, %(address)s, %(brand)s, %(customername)s,%(deleverydate)s,%(email)s,%(modelname)s,%(orddate)s,%(phone)s,%(price)s,%(producttype)s,%(serialno)s)
        """, {'orderid': oid, 'address': add, 'brand': brand, 'customername': name, 'deleverydate': ddate, 'email': email, 'modelname': model, 'orddate': odate, 'phone': phone, 'price': price, 'producttype': product, 'serialno': serial}
    )
    ordermsg = "Your Order  for "+oid+" "+brand+" "+product+" "+model + \
        "  worth "+price+" has been recieved. You can expect delivery by "+ddate
    print(ordermsg)
    msg = Message('Order Placed:',
                  sender='rcbbrandcollection@gmail.com', recipients=[email])
    msg.body = ordermsg
    mail.send(msg)

    sn = int(serial)

    rows = csession.execute('select * from products where serialno=%(serialno)s',
                            {'serialno': sn})
    r = []
    for pdt_row in rows:
        r.append(pdt_row.stocks)
    print("This is Oldstoks : ", r[0])
    stock = r[0]-1
    print("This is Updated Stocks : ", stock)

    csession.execute(
        """
    UPDATE products set stocks=%(stocks)s where serialno=%(serialno)s
    """,
        {'serialno': sn, 'stocks': stock}
    )

    return render_template('recieved.html', msg="Thank you for ordering On RCB Grand Collections,..")


@app.route('/myorders/<email>', methods=['GET'])
def myorders(email):
    mail = email
    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from orders where email=%(email)s ALLOW FILTERING',
                            {'email': mail})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.orderid, pdt_row.serialno, pdt_row.producttype, pdt_row.brand,
                 pdt_row.modelname, pdt_row.price, pdt_row.orddate, pdt_row.deleverydate])
    r = tuple(r)
    print()
    return render_template('ordered_items.html', r=r, l=custord, zip=zip, acc=account[0], msg="")


@app.route('/order/delete/<oid>')
def orderdelete(oid):
    orderid = oid

    csession = cassandra_connect()
    csession.execute('USE trial')

    rows = csession.execute('select * from orders where orderid=%(orderid)s',
                            {'orderid': orderid})
    r = []
    for pdt_row in rows:
        r.append([pdt_row.orderid, pdt_row.email, pdt_row.serialno, pdt_row.producttype,
                 pdt_row.brand, pdt_row.modelname, pdt_row.price, pdt_row.orddate, pdt_row.deleverydate])
    r = tuple(r)
    c = []
    for row in r:
        for col in row:
            c.append(col)
            print(col)
    print("serialno : ", c[2])
    sn = int(c[2])

    deletemsg = c[4]+" "+c[5]+" "+c[3]+" in your orders with order id " + \
        c[0]+" ordered on "+c[7]+" has been cancelled"
    print(deletemsg)
    msg = Message('Order Cancelled',
                  sender='rcbbrandcollection@gmail.com', recipients=[c[1]])
    msg.body = deletemsg
    mail.send(msg)

    csession.execute(
        """
    DELETE from orders where orderid=%(orderid)s
    """,
        {'orderid': orderid})

    rows2 = csession.execute('select * from orders where email=%(email)s ALLOW FILTERING',
                             {'email': account[0]})
    r2 = []
    for pdt_row in rows2:
        r2.append([pdt_row.orderid, pdt_row.serialno, pdt_row.producttype, pdt_row.brand,
                  pdt_row.modelname, pdt_row.price, pdt_row.orddate, pdt_row.deleverydate])
    r2 = tuple(r2)

    rows3 = csession.execute('select * from products where serialno=%(serialno)s',
                             {'serialno': sn})
    r3 = []
    for pdt_row in rows3:
        r3.append(pdt_row.stocks)
    print("This is Oldstoks : ", r3[0])
    stock = r3[0]+1
    print("This is Updated Stocks : ", stock)

    csession.execute(
        """
    UPDATE products set stocks=%(stocks)s where serialno=%(serialno)s
    """,
        {'serialno': sn, 'stocks': stock}
    )

    message = "Your order with Order Id = "+oid + \
        " Is Cancelled.. You will Get more details through mail"
    return render_template('ordered_items.html', r=r2, l=custord, zip=zip, acc=account[0], msg=message)


if __name__ == "__main__":
    app.run(debug=True)
