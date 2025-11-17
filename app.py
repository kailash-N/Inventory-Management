from sqlalchemy.orm import sessionmaker
from model import Customer, Product, Stock, Purchase, Sale, engine
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from sqlalchemy import func, extract

Session = sessionmaker(bind=engine)

app = Flask(__name__)
CORS(app)

# Helper function to get a new session for each request
def get_session():
    return Session()

# ==================== PRODUCTS ====================
@app.route("/api/products", methods=["GET"])
def getAllProducts():
    session = get_session()
    try:
        products = session.query(Product).all()
        result = [
            {
                "product_id": p.product_id, 
                "name": p.name,
                "description": p.description,
                "category": p.category
            }
            for p in products
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch products", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products/<int:productId>", methods=["GET"])
def getSingleProduct(productId):
    session = get_session()
    try:
        product = session.query(Product).filter_by(product_id=productId).first()
        if not product:
            return jsonify({"error": "Not found", "message": f"Product with id {productId} not Found"}), 404
        result = {
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "category": product.category
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch products", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products", methods=["POST"])
def createProduct():
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        if not data.get('name'):
            return jsonify({"error": "Bad Request", "message": "Product name is required"}), 400
        
        existing_product = session.query(Product).filter_by(name=data["name"]).first()
        if existing_product:
            return jsonify({"error": "Conflict", "message": "Product with this name already exists"}), 409
        
        newProduct = Product(
            name=data["name"],
            description=data.get("description"),
            category=data.get("category")
        )

        session.add(newProduct)
        session.commit()

        result = {
            "product_id": newProduct.product_id,
            "name": newProduct.name,
            "description": newProduct.description,
            "category": newProduct.category
        }
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to create product", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products/<int:productId>", methods=["PUT"])
def updateProduct(productId):
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        product = session.query(Product).filter_by(product_id=productId).first()
        if not product:
            return jsonify({"error": "Not Found", "message": f"Product with id {productId} not found"}), 404
        
        if not data.get("name"):
            return jsonify({"error": "Bad Request", "message": "Product name is required"}), 400
        
        existing_product = session.query(Product).filter_by(name=data["name"]).filter(Product.product_id != productId).first()
        if existing_product:
            return jsonify({"error": "Conflict", "message": "Product with this name already exists"}), 409
        
        product.name = data["name"]
        product.description = data.get("description")
        product.category = data.get("category")
        session.commit()
        
        result = {
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "category": product.category
        }
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update product", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products/<int:productId>", methods=["DELETE"])
def deleteProduct(productId):
    session = get_session()
    try:
        product = session.query(Product).filter_by(product_id=productId).first()
        if not product:
            return jsonify({"error": "Not Found", "message": f"Product with id {productId} not found"}), 404
        session.delete(product)
        session.commit()
        
        products = session.query(Product).all()
        result = [
            {
                "product_id": p.product_id, 
                "name": p.name,
                "description": p.description,
                "category": p.category
            }
            for p in products
        ]
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to delete product", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products/categories", methods=["GET"])
def getAllProductsCategories():
    session = get_session()
    try:
        categories = session.query(Product.category).filter(Product.category.isnot(None)).distinct().all()
        result = [category[0] for category in categories if category[0]]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch categories", "message": str(e)}), 500
    finally:
        session.close()

# ==================== STOCK ====================
@app.route("/api/stock", methods=["GET"])
def getAllStock():
    session = get_session()
    try:
        stocks = session.query(
            Stock.stock_id,
            Stock.product_id,
            Stock.available_quantity,
            Stock.cost_price,
            Stock.selling_price,
            Stock.last_updated,
            Product.product_id.label("p_id"),
            Product.name.label("p_name"),
            Product.category.label("p_category")
        ).join(Product, Stock.product_id == Product.product_id, isouter=True).all()
        
        result = [
            {
                "stock_id": stock.stock_id,
                "product_id": stock.product_id,
                "available_quantity": stock.available_quantity,
                "cost_price": float(stock.cost_price),
                "selling_price": float(stock.selling_price),
                "last_updated": stock.last_updated.isoformat() if stock.last_updated else None,
                "product": {
                    "product_id": stock.p_id,
                    "name": stock.p_name,
                    "category": stock.p_category
                }
            }
            for stock in stocks
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "failed to fetch stocks detail", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/stock/<int:stockId>", methods=["GET"])
def getSingleStock(stockId):
    session = get_session()
    try:
        stock = session.query(Stock).filter_by(stock_id=stockId).first()
        if not stock:
            return jsonify({"error": "Not Found", "message": f"stock not found for stock_id {stockId}"}), 404
        
        product = session.query(Product).filter_by(product_id=stock.product_id).first()
        
        result = {
            "stock_id": stock.stock_id,
            "product_id": stock.product_id,
            "available_quantity": stock.available_quantity,
            "cost_price": float(stock.cost_price),
            "selling_price": float(stock.selling_price),
            "last_updated": stock.last_updated.isoformat() if stock.last_updated else None,
            "product": {
                "product_id": product.product_id if product else None,
                "name": product.name if product else None,
                "category": product.category if product else None
            }
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "failed to fetch stock detail", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/stock", methods=["POST"])
def createStock():
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        if not data.get('product_id'):
            return jsonify({"error": "Bad Request", "message": "Product id is required"}), 400
        
        existing_stock = session.query(Stock).filter_by(product_id=data["product_id"]).first()
        if existing_stock:
            return jsonify({"error": "Conflict", "message": "Stock with this product_id already exists"}), 409
        
        existing_product = session.query(Product).filter_by(product_id=data["product_id"]).first()
        if not existing_product:
            return jsonify({"error": "Conflict", "message": "product with this product_id not exists"}), 409
        
        newStock = Stock(
            product_id=data["product_id"],
            available_quantity=data.get("available_quantity", 0),
            cost_price=data.get("cost_price", 0.0),
            selling_price=data.get("selling_price", 0.0)
        )

        session.add(newStock)
        session.commit()
        
        result = {
            "stock_id": newStock.stock_id,
            "product_id": newStock.product_id,
            "available_quantity": newStock.available_quantity,
            "cost_price": float(newStock.cost_price),
            "selling_price": float(newStock.selling_price)
        }
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to create stock", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/stock/<int:stockId>", methods=["PUT"])
def updateStock(stockId):
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400

        stock = session.query(Stock).filter_by(stock_id=stockId).first()
        if not stock:
            return jsonify({"error": "Not Found", "message": f"Stock with id {stockId} not found"}), 404

        if data.get('product_id'):
            stock.product_id = data["product_id"]
        if data.get('available_quantity') is not None:
            stock.available_quantity = data["available_quantity"]
        if data.get('cost_price'):
            stock.cost_price = data["cost_price"]
        if data.get('selling_price'):
            stock.selling_price = data["selling_price"]
        
        session.commit()

        result = {
            "stock_id": stock.stock_id,
            "product_id": stock.product_id,
            "available_quantity": stock.available_quantity,
            "cost_price": float(stock.cost_price),
            "selling_price": float(stock.selling_price)
        }
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update stock", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/stock/low", methods=["GET"])
def getLowStockItems():
    session = get_session()
    try:
        threshold = request.args.get('threshold', 5, type=int)
        
        low_stock_query = session.query(Stock).filter(
            Stock.available_quantity <= threshold
        ).join(Product)
        
        low_stock_items = low_stock_query.all()
        
        result = []
        out_of_stock_count = 0
        critical_count = 0
        total_value = 0
        
        for item in low_stock_items:
            if item.available_quantity == 0:
                out_of_stock_count += 1
                status = "out_of_stock"
            elif item.available_quantity <= 2:
                critical_count += 1
                status = "critical"
            else:
                status = "low_stock"
            
            total_value += (item.available_quantity * float(item.cost_price))
            
            result.append({
                "stock_id": item.stock_id,
                "product_id": item.product_id,
                "available_quantity": item.available_quantity,
                "cost_price": float(item.cost_price),
                "selling_price": float(item.selling_price),
                "last_updated": item.last_updated.isoformat() if item.last_updated else None,
                "status": status,
                "product": {
                    "product_id": item.product.product_id,
                    "name": item.product.name,
                    "description": item.product.description,
                    "category": item.product.category
                }
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch low stock items", "message": str(e)}), 500
    finally:
        session.close()

# ==================== CUSTOMERS ====================
@app.route("/api/customers", methods=["GET"])
def getAllCustomers():
    session = get_session()
    try:
        customers = session.query(Customer).all()
        result = [
            {
                "c_id": customer.c_id,
                "name": customer.name,
                "gstno": customer.gstno,
                "address": customer.address,
                "phone_no": customer.phone_no,
                "email": customer.email
            }
            for customer in customers
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "failed fetch customer details", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/customers/<int:customerId>", methods=["GET"])
def getSingleCustomer(customerId):
    session = get_session()
    try:
        customer = session.query(Customer).filter_by(c_id=customerId).first()
        if not customer:
            return jsonify({"error": "Not Found", "message": f"Customer with id {customerId} not found"}), 404
        
        result = {
            "c_id": customer.c_id,
            "name": customer.name,
            "gstno": customer.gstno,
            "address": customer.address,
            "phone_no": customer.phone_no,
            "email": customer.email
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "failed fetch customer details", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/customers", methods=["POST"])
def createCustomer():
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        if not data.get("name"):
            return jsonify({"error": "Bad Request", "message": "Customer name is required"}), 400

        if not data.get("address"):
            return jsonify({"error": "Bad Request", "message": "Customer address is required"}), 400
        
        if not data.get("phone_no"):
            return jsonify({"error": "Bad Request", "message": "Customer phone no is required"}), 400
        
        newCustomer = Customer(
            name=data.get("name"),
            gstno=data.get("gstno"),
            address=data.get("address"),
            phone_no=data.get("phone_no"),
            email=data.get("email")
        )
        session.add(newCustomer)
        session.commit()

        result = {
            "c_id": newCustomer.c_id,
            "name": newCustomer.name,
            "gstno": newCustomer.gstno,
            "address": newCustomer.address,
            "phone_no": newCustomer.phone_no,
            "email": newCustomer.email
        }
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to create customer", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/customers/<int:customerId>", methods=["PUT"])
def updateCustomer(customerId):
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        customer = session.query(Customer).filter_by(c_id=customerId).first()
        if not customer:
            return jsonify({"error": "Not Found", "message": f"Customer with id {customerId} not found"}), 404
        
        customer.name = data.get("name", customer.name)
        customer.gstno = data.get("gstno", customer.gstno)
        customer.address = data.get("address", customer.address)
        customer.phone_no = data.get("phone_no", customer.phone_no)
        customer.email = data.get("email", customer.email)

        session.commit()
        result = {
            "c_id": customer.c_id,
            "name": customer.name,
            "gstno": customer.gstno,
            "address": customer.address,
            "phone_no": customer.phone_no,
            "email": customer.email
        }
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update customer", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/customers/<int:customerId>", methods=["DELETE"])
def deleteCustomer(customerId):
    session = get_session()
    try:
        customer = session.query(Customer).filter_by(c_id=customerId).first()
        if not customer:
            return jsonify({"error": "Not Found", "message": f"customer with id {customerId} not found"}), 404

        session.delete(customer)
        session.commit()
        
        remaining_customers = session.query(Customer).all()
        result = [
            {
                "c_id": remaining_customer.c_id,
                "name": remaining_customer.name,
                "gstno": remaining_customer.gstno,
                "address": remaining_customer.address,
                "phone_no": remaining_customer.phone_no,
                "email": remaining_customer.email
            }
            for remaining_customer in remaining_customers
        ]
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to delete customer", "message": str(e)}), 500
    finally:
        session.close()

# ==================== PURCHASES ====================
@app.route("/api/purchases", methods=["GET"])
def getAllPurchases():
    session = get_session()
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        is_paid = request.args.get('is_paid')
        
        query = session.query(Purchase).join(Product)
        
        if date_from:
            query = query.filter(Purchase.purchase_date >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Purchase.purchase_date <= datetime.fromisoformat(date_to))
        if is_paid is not None:
            query = query.filter(Purchase.is_paid == (is_paid.lower() == 'true'))
        
        purchases = query.all()
        
        result = [
            {
                "purchase_id": p.purchase_id,
                "product_id": p.product_id,
                "quantity": p.quantity,
                "cost_price": float(p.cost_price),
                "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
                "serial_no": p.serial_no,
                "is_paid": p.is_paid,
                "product": {
                    "product_id": p.product.product_id,
                    "name": p.product.name
                }
            }
            for p in purchases
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch purchases", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/purchases/<int:purchaseId>", methods=["GET"])
def getSinglePurchase(purchaseId):
    session = get_session()
    try:
        purchase = session.query(Purchase).filter_by(purchase_id=purchaseId).first()
        if not purchase:
            return jsonify({"error": "Not Found", "message": f"Purchase with id {purchaseId} not found"}), 404
        
        result = {
            "purchase_id": purchase.purchase_id,
            "product_id": purchase.product_id,
            "quantity": purchase.quantity,
            "cost_price": float(purchase.cost_price),
            "purchase_date": purchase.purchase_date.isoformat() if purchase.purchase_date else None,
            "serial_no": purchase.serial_no,
            "is_paid": purchase.is_paid,
            "product": {
                "product_id": purchase.product.product_id,
                "name": purchase.product.name
            }
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch purchase", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/purchases", methods=["POST"])
def createPurchase():
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        if not data.get('product_id'):
            return jsonify({"error": "Bad Request", "message": "Product ID is required"}), 400
        
        if not data.get('quantity'):
            return jsonify({"error": "Bad Request", "message": "Quantity is required"}), 400
        
        if not data.get('cost_price'):
            return jsonify({"error": "Bad Request", "message": "Cost price is required"}), 400
        
        # Check if product exists
        product = session.query(Product).filter_by(product_id=data["product_id"]).first()
        if not product:
            return jsonify({"error": "Not Found", "message": "Product not found"}), 404
        
        newPurchase = Purchase(
            product_id=data["product_id"],
            quantity=data["quantity"],
            cost_price=data["cost_price"],
            serial_no=data.get("serial_no"),
            is_paid=data.get("is_paid", False)
        )
        
        session.add(newPurchase)
        
        # Update stock
        stock = session.query(Stock).filter_by(product_id=data["product_id"]).first()
        if stock:
            stock.available_quantity += data["quantity"]
            stock.cost_price = data["cost_price"]
        else:
            newStock = Stock(
                product_id=data["product_id"],
                available_quantity=data["quantity"],
                cost_price=data["cost_price"],
                selling_price=data.get("selling_price", data["cost_price"] * 1.2)
            )
            session.add(newStock)
        
        session.commit()
        
        result = {
            "purchase_id": newPurchase.purchase_id,
            "product_id": newPurchase.product_id,
            "quantity": newPurchase.quantity,
            "cost_price": float(newPurchase.cost_price),
            "purchase_date": newPurchase.purchase_date.isoformat() if newPurchase.purchase_date else None,
            "serial_no": newPurchase.serial_no,
            "is_paid": newPurchase.is_paid
        }
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to create purchase", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/purchases/<int:purchaseId>", methods=["PUT"])
def updatePurchase(purchaseId):
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        purchase = session.query(Purchase).filter_by(purchase_id=purchaseId).first()
        if not purchase:
            return jsonify({"error": "Not Found", "message": f"Purchase with id {purchaseId} not found"}), 404
        
        old_quantity = purchase.quantity
        
        if data.get('quantity'):
            purchase.quantity = data["quantity"]
        if data.get('cost_price'):
            purchase.cost_price = data["cost_price"]
        if data.get('serial_no') is not None:
            purchase.serial_no = data["serial_no"]
        if data.get('is_paid') is not None:
            purchase.is_paid = data["is_paid"]
        
        # Adjust stock if quantity changed
        if data.get('quantity') and data['quantity'] != old_quantity:
            stock = session.query(Stock).filter_by(product_id=purchase.product_id).first()
            if stock:
                stock.available_quantity += (data['quantity'] - old_quantity)
        
        session.commit()
        
        result = {
            "purchase_id": purchase.purchase_id,
            "product_id": purchase.product_id,
            "quantity": purchase.quantity,
            "cost_price": float(purchase.cost_price),
            "purchase_date": purchase.purchase_date.isoformat() if purchase.purchase_date else None,
            "serial_no": purchase.serial_no,
            "is_paid": purchase.is_paid
        }
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update purchase", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/purchases/<int:purchaseId>", methods=["DELETE"])
def deletePurchase(purchaseId):
    session = get_session()
    try:
        purchase = session.query(Purchase).filter_by(purchase_id=purchaseId).first()
        if not purchase:
            return jsonify({"error": "Not Found", "message": f"Purchase with id {purchaseId} not found"}), 404
        
        # Adjust stock
        stock = session.query(Stock).filter_by(product_id=purchase.product_id).first()
        if stock:
            stock.available_quantity -= purchase.quantity
        
        session.delete(purchase)
        session.commit()
        return "", 204
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to delete purchase", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/purchases/<int:purchaseId>/payment", methods=["PUT"])
def updatePurchasePaymentStatus(purchaseId):
    session = get_session()
    try:
        data = request.json
        purchase = session.query(Purchase).filter_by(purchase_id=purchaseId).first()
        if not purchase:
            return jsonify({"error": "Not Found", "message": f"Purchase with id {purchaseId} not found"}), 404
        
        purchase.is_paid = data.get("is_paid", purchase.is_paid)
        session.commit()
        
        return jsonify({"purchase_id": purchase.purchase_id, "is_paid": purchase.is_paid}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update payment status", "message": str(e)}), 500
    finally:
        session.close()

# ==================== SALES ====================
@app.route("/api/sales", methods=["GET"])
def getAllSales():
    session = get_session()
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        is_paid = request.args.get('is_paid')
        customer_id = request.args.get('customer_id', type=int)
        
        query = session.query(Sale).join(Customer).join(Product)
        
        if date_from:
            query = query.filter(Sale.sale_date >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Sale.sale_date <= datetime.fromisoformat(date_to))
        if is_paid is not None:
            query = query.filter(Sale.is_paid == (is_paid.lower() == 'true'))
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        
        sales = query.all()
        
        result = [
            {
                "sale_id": s.sale_id,
                "customer_id": s.customer_id,
                "product_id": s.product_id,
                "quantity": s.quantity,
                "selling_price": float(s.selling_price),
                "discount_percentage": float(s.discount_percentage),
                "total_amount": float(s.total_amount),
                "sale_date": s.sale_date.isoformat() if s.sale_date else None,
                "serial_numbers": s.serial_numbers,
                "is_paid": s.is_paid,
                "customer": {
                    "c_id": s.customer.c_id,
                    "name": s.customer.name
                },
                "product": {
                    "product_id": s.product.product_id,
                    "name": s.product.name
                }
            }
            for s in sales
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch sales", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/sales/<int:saleId>", methods=["GET"])
def getSingleSale(saleId):
    session = get_session()
    try:
        sale = session.query(Sale).filter_by(sale_id=saleId).first()
        if not sale:
            return jsonify({"error": "Not Found", "message": f"Sale with id {saleId} not found"}), 404
        
        result = {
            "sale_id": sale.sale_id,
            "customer_id": sale.customer_id,
            "product_id": sale.product_id,
            "quantity": sale.quantity,
            "selling_price": float(sale.selling_price),
            "discount_percentage": float(sale.discount_percentage),
            "total_amount": float(sale.total_amount),
            "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
            "serial_numbers": sale.serial_numbers,
            "is_paid": sale.is_paid,
            "customer": {
                "c_id": sale.customer.c_id,
                "name": sale.customer.name
            },
            "product": {
                "product_id": sale.product.product_id,
                "name": sale.product.name
            }
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch sale", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/sales", methods=["POST"])
def createSale():
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        if not data.get('customer_id'):
            return jsonify({"error": "Bad Request", "message": "Customer ID is required"}), 400
        
        if not data.get('product_id'):
            return jsonify({"error": "Bad Request", "message": "Product ID is required"}), 400
        
        if not data.get('quantity'):
            return jsonify({"error": "Bad Request", "message": "Quantity is required"}), 400
        
        if not data.get('selling_price'):
            return jsonify({"error": "Bad Request", "message": "Selling price is required"}), 400
        
        if not data.get('total_amount'):
            return jsonify({"error": "Bad Request", "message": "Total amount is required"}), 400
        
        # Check if customer exists
        customer = session.query(Customer).filter_by(c_id=data["customer_id"]).first()
        if not customer:
            return jsonify({"error": "Not Found", "message": "Customer not found"}), 404
        
        # Check if product exists
        product = session.query(Product).filter_by(product_id=data["product_id"]).first()
        if not product:
            return jsonify({"error": "Not Found", "message": "Product not found"}), 404
        
        # Check stock availability
        stock = session.query(Stock).filter_by(product_id=data["product_id"]).first()
        if not stock or stock.available_quantity < data["quantity"]:
            return jsonify({"error": "Bad Request", "message": "Insufficient stock"}), 400
        
        newSale = Sale(
            customer_id=data["customer_id"],
            product_id=data["product_id"],
            quantity=data["quantity"],
            selling_price=data["selling_price"],
            discount_percentage=data.get("discount_percentage", 0.0),
            total_amount=data["total_amount"],
            serial_numbers=data.get("serial_numbers"),
            is_paid=data.get("is_paid", False)
        )
        
        session.add(newSale)
        
        # Update stock
        stock.available_quantity -= data["quantity"]
        
        session.commit()
        
        result = {
            "sale_id": newSale.sale_id,
            "customer_id": newSale.customer_id,
            "product_id": newSale.product_id,
            "quantity": newSale.quantity,
            "selling_price": float(newSale.selling_price),
            "discount_percentage": float(newSale.discount_percentage),
            "total_amount": float(newSale.total_amount),
            "sale_date": newSale.sale_date.isoformat() if newSale.sale_date else None,
            "serial_numbers": newSale.serial_numbers,
            "is_paid": newSale.is_paid
        }
        return jsonify(result), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to create sale", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/sales/<int:saleId>", methods=["PUT"])
def updateSale(saleId):
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        sale = session.query(Sale).filter_by(sale_id=saleId).first()
        if not sale:
            return jsonify({"error": "Not Found", "message": f"Sale with id {saleId} not found"}), 404
        
        old_quantity = sale.quantity
        
        if data.get('quantity'):
            # Check stock if quantity is being increased
            stock = session.query(Stock).filter_by(product_id=sale.product_id).first()
            quantity_diff = data['quantity'] - old_quantity
            if quantity_diff > 0 and (not stock or stock.available_quantity < quantity_diff):
                return jsonify({"error": "Bad Request", "message": "Insufficient stock"}), 400
            
            sale.quantity = data["quantity"]
            
            # Adjust stock
            if stock:
                stock.available_quantity -= quantity_diff
        
        if data.get('selling_price'):
            sale.selling_price = data["selling_price"]
        if data.get('discount_percentage') is not None:
            sale.discount_percentage = data["discount_percentage"]
        if data.get('total_amount'):
            sale.total_amount = data["total_amount"]
        if data.get('serial_numbers') is not None:
            sale.serial_numbers = data["serial_numbers"]
        if data.get('is_paid') is not None:
            sale.is_paid = data["is_paid"]
        
        session.commit()
        
        result = {
            "sale_id": sale.sale_id,
            "customer_id": sale.customer_id,
            "product_id": sale.product_id,
            "quantity": sale.quantity,
            "selling_price": float(sale.selling_price),
            "discount_percentage": float(sale.discount_percentage),
            "total_amount": float(sale.total_amount),
            "sale_date": sale.sale_date.isoformat() if sale.sale_date else None,
            "serial_numbers": sale.serial_numbers,
            "is_paid": sale.is_paid
        }
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update sale", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/sales/<int:saleId>", methods=["DELETE"])
def deleteSale(saleId):
    session = get_session()
    try:
        sale = session.query(Sale).filter_by(sale_id=saleId).first()
        if not sale:
            return jsonify({"error": "Not Found", "message": f"Sale with id {saleId} not found"}), 404
        
        # Return stock
        stock = session.query(Stock).filter_by(product_id=sale.product_id).first()
        if stock:
            stock.available_quantity += sale.quantity
        
        session.delete(sale)
        session.commit()
        return "", 204
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to delete sale", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/sales/<int:saleId>/payment", methods=["PUT"])
def updateSalePaymentStatus(saleId):
    session = get_session()
    try:
        data = request.json
        sale = session.query(Sale).filter_by(sale_id=saleId).first()
        if not sale:
            return jsonify({"error": "Not Found", "message": f"Sale with id {saleId} not found"}), 404
        
        sale.is_paid = data.get("is_paid", sale.is_paid)
        session.commit()
        
        return jsonify({"sale_id": sale.sale_id, "is_paid": sale.is_paid}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update payment status", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/sales/monthly", methods=["GET"])
def getMonthlySales():
    session = get_session()
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # Get sales for the specified month
        sales = session.query(Sale).filter(
            extract('year', Sale.sale_date) == year,
            extract('month', Sale.sale_date) == month
        ).all()
        
        total = sum(float(s.total_amount) for s in sales)
        count = len(sales)
        paid = sum(float(s.total_amount) for s in sales if s.is_paid)
        unpaid = sum(float(s.total_amount) for s in sales if not s.is_paid)
        
        result = {
            "total": round(total, 2),
            "count": count,
            "paid": round(paid, 2),
            "unpaid": round(unpaid, 2),
            "year": year,
            "month": month
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch monthly sales", "message": str(e)}), 500
    finally:
        session.close()

# ==================== DASHBOARD / ANALYTICS ====================
@app.route("/api/activities/recent", methods=["GET"])
def getRecentActivities():
    session = get_session()
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get recent sales
        recent_sales = session.query(Sale).order_by(Sale.sale_date.desc()).limit(limit // 2).all()
        
        # Get recent purchases
        recent_purchases = session.query(Purchase).order_by(Purchase.purchase_date.desc()).limit(limit // 2).all()
        
        activities = []
        
        for sale in recent_sales:
            activities.append({
                "type": "SALE",
                "description": f"Sale of {sale.quantity} x {sale.product.name} to {sale.customer.name}",
                "timestamp": sale.sale_date.isoformat() if sale.sale_date else None
            })
        
        for purchase in recent_purchases:
            activities.append({
                "type": "PURCHASE",
                "description": f"Purchase of {purchase.quantity} x {purchase.product.name}",
                "timestamp": purchase.purchase_date.isoformat() if purchase.purchase_date else None
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
        
        return jsonify(activities[:limit]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch recent activities", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/dashboard/stats", methods=["GET"])
def getDashboardStats():
    session = get_session()
    try:
        # Total products
        total_products = session.query(Product).count()
        
        # Total customers
        total_customers = session.query(Customer).count()
        
        # Low stock items (threshold of 5)
        low_stock_items = session.query(Stock).filter(Stock.available_quantity <= 5).count()
        
        # Monthly sales (current month)
        now = datetime.now()
        monthly_sales_data = session.query(func.sum(Sale.total_amount)).filter(
            extract('year', Sale.sale_date) == now.year,
            extract('month', Sale.sale_date) == now.month
        ).scalar()
        monthly_sales = float(monthly_sales_data) if monthly_sales_data else 0.0
        
        # Monthly purchases (current month)
        monthly_purchases_data = session.query(
            func.sum(Purchase.quantity * Purchase.cost_price)
        ).filter(
            extract('year', Purchase.purchase_date) == now.year,
            extract('month', Purchase.purchase_date) == now.month
        ).scalar()
        monthly_purchases = float(monthly_purchases_data) if monthly_purchases_data else 0.0
        
        # Pending payments
        sales_pending = session.query(func.sum(Sale.total_amount)).filter(
            Sale.is_paid == False
        ).scalar()
        
        purchases_pending = session.query(
            func.sum(Purchase.quantity * Purchase.cost_price)
        ).filter(
            Purchase.is_paid == False
        ).scalar()
        
        result = {
            "total_products": total_products,
            "total_customers": total_customers,
            "low_stock_items": low_stock_items,
            "monthly_sales": round(monthly_sales, 2),
            "monthly_purchases": round(monthly_purchases, 2),
            "pending_payments": {
                "sales": round(float(sales_pending) if sales_pending else 0.0, 2),
                "purchases": round(float(purchases_pending) if purchases_pending else 0.0, 2)
            }
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch dashboard stats", "message": str(e)}), 500
    finally:
        session.close()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method Not Allowed", "message": "Method not allowed for this endpoint"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=2004)