from sqlalchemy.orm import sessionmaker
from model import Customer, engine
from flask import Flask, request, jsonify

Session = sessionmaker(bind=engine)
session = Session()

app = Flask(__name__)

@app.route("/customers",methods=["GET"])
def get_customers():
    customers = session.query(Customer).all()
    result = [{"id": c.c_id, "gst_no": c.gstno, "address": c.address, "phone_no": c.phone_no, "email": c.email} for c in customers]
    return jsonify(result)

@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.json
    new_customer = Customer(
        name=data['name'],
        gstno=data.get('gstno'),
        address=data['address'],
        phone_no=data['phone_no'],
        email=data.get('email')
    )
    session.add(new_customer)
    session.commit()
    session.refresh(new_customer)
    return jsonify({'message': 'Customer added', 'id': new_customer.c_id})

if __name__ == "__main__":
    app.run(debug=True)