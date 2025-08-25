from sqlalchemy.orm import sessionmaker, joinedload
from model import Customer, Product, Stock, engine
from flask import Flask, request, jsonify
from flask_cors import CORS

Session = sessionmaker(bind=engine)

app = Flask(__name__)
CORS(app)
# Helper function to get a new session for each request
def get_session():
    return Session()

#products
@app.route("/api/products" , methods=["GET"])
def getAllProduts():
    session = get_session()
    try:
        products = session.query(Product).all()
        result = [
            {
                "product_id": p.product_id, 
                "name":p.name ,
                "description":p.description,
                "category":p.category
            }
            for p in products
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch products", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products/<int:productId>" , methods=["GET"])
def getSingleProduct(productId):
    session = get_session()
    try:
        product = session.query(Product).filter_by(product_id=productId).first()
        if not product:
            return jsonify({"error":"Not found", "message": f"Product with id {productId} not Found"}), 404
        result = {
            "product_id": product.product_id,
            "name":product.name ,
            "description":product.description,
            "category":product.category
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch products", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products" , methods=["POST"])
def createProduct():
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        if not data.get('name'):
            return jsonify({"error": "Bad Request", "message": "Product name is required"}), 400
        
        # Check if product with same name already exists
        existing_product = session.query(Product).filter_by(name=data["name"]).first()
        if existing_product:
            return jsonify({"error": "Conflict", "message": "Product with this name already exists"}), 409
        
        newProduct = Product(
            name = data["name"],
            description = data["description"],
            category = data["category"]
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

@app.route("/api/products/<int:productId>" , methods=["PUT"])
def updateProduct(productId):
    session = get_session()
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400
        
        product = session.query(Product).filter_by(product_id=productId).first()
        if not product:
            return jsonify({"error": "Not Found", "message": f"Product with id {productId} not found"}), 404
        
        # Validate required fields
        if not data.get("name"):
            return jsonify({"error": "Bad Request", "message": "Product name is required"}), 400
        
        # Check if another product with same name already exists
        existing_product = session.query(Product).filter_by(name=data["name"]).filter(Product.product_id != productId).first()
        if existing_product:
            return jsonify({"error": "Conflict", "message": "Product with this name already exists"}), 409
        
        product.name = data["name"]
        product.description = data["description"]
        product.category = data["category"]
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

@app.route("/api/products/<int:productId>" , methods=["DELETE"])
def deleteProduct(productId):
    session = get_session()
    try:
        product = session.query(Product).filter_by(product_id=productId).first()
        if not product:
            return jsonify({"error": "Not Found", "message": f"Product with id {productId} not found"}), 404
        session.delete(product)
        session.commit()
        print("Product deleted successfully")
        return "", 204
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to delete product", "message": str(e)}), 500
    finally:
        session.close()

@app.route("/api/products/categories" , methods=["GET"])
def getAllProdutsCategories():
    session = get_session()
    try:
        categories = session.query(Product.category).filter(Product.category.isnot(None)).distinct().all()
        result = [category[0] for category in categories if category[0]]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch categories", "message": str(e)}), 500
    finally:
        session.close()

#stock
@app.route("/api/stock",  methods=["GET"])
def getAllStock():
    session = get_session()
    try:
        # Join Stock and Product
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
                "stock_id":stock.stock_id,
                "product_id": stock.product_id,
                "available_quantity": stock.available_quantity,
                "cost_price": stock.cost_price,
                "selling_price": stock.selling_price,
                "last_updated": stock.last_updated,
                "product":{
                    "product_id": stock.p_id,
                    "name": stock.p_name,
                    "category": stock.p_category
                }
            }
            for stock in stocks
        ]
        return jsonify(result),200
    except Exception as e:
        return jsonify({"error":"failed to fetch stocks detail", "message":str(e)}),500
    finally:
        session.close()

@app.route("/api/stock/<int:stockId>", methods=["GET"])
def getSingleStock(stockId):
    session = get_session()
    try:
        stock = session.query(Stock).filter_by(stock_id = stockId).first()
        if not stock:
            return jsonify({"error":"Not Found", "message":f"stock not found for stock_id{stockId}"}) , 404
        result = {
            "stock_id":stock["stock_id"],
                "product_id": stock["product_id"],
                "available_quantity": stock["available_quantity"],
                "cost_price": stock["cost_price"],
                "selling_price": stock["selling_price"],
                "last_updated": stock["last_updated"],
                "product":{
                    "product_id": session.query(Product.product_id).filter_by(product_id = stock["product_id"]).first(),
                    "name": session.query(Product.name).filter_by(product_id = stock["product_id"]).first(),
                    "category": session.query(Product.category).filter_by(product_id = stock["product_id"]).first()
                }
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error":"failed to fetch stock detail" , "message":str(e)}), 500
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
        
        if not data.get('available_quantity'):
            return jsonify({"error": "Bad Request", "message": "available quantity is required"}), 400
        
        if not data.get('cost_price'):
            return jsonify({"error": "Bad Request", "message": "cost price is required"}), 400
        
        if not data.get('selling_price'):
            return jsonify({"error": "Bad Request", "message": "selling price is required"}), 400
        
        # Check if stock same product_id already exists
        existing_stock = session.query(Stock).filter_by(product_id=data["product_id"]).first()
        if existing_stock:
            return jsonify({"error": "Conflict", "message": "Stock with this product_id already exists"}), 409
        
        # Check if product_id exists in products
        existing_product = session.query(Product).filter_by(product_id=data["product_id"]).first()
        if not existing_product:
            return jsonify({"error": "Conflict", "message": "product with this product_id not exists"}), 409
        
        newStock = Stock(
            product_id = data["product_id"],
            available_quantity = data["available_quantity"],
            cost_price = data["cost_price"],
            selling_price = data["selling_price"]
        )

        session.add(newStock)
        session.commit()
        
        result = {
            "stock_id": newStock.stock_id,
            "product_id": newStock.product_id,
            "available_quantity": newStock.available_quantity,
            "cost_price": newStock.cost_price,
            "selling_price": newStock.selling_price
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

        if not data.get('product_id'):
            return jsonify({"error": "Bad Request", "message": "Product id is required"}), 400
        
        if not data.get('available_quantity'):
            return jsonify({"error": "Bad Request", "message": "available quantity is required"}), 400
        
        if not data.get('cost_price'):
            return jsonify({"error": "Bad Request", "message": "cost price is required"}), 400
        
        if not data.get('selling_price'):
            return jsonify({"error": "Bad Request", "message": "selling price is required"}), 400

        stock = session.query(Stock).filter_by(stock_id = stockId).first()
        if not stock:
            return jsonify({"error": "Not Found", "message": f"Stock with id {stockId} not found"}), 404

        # Check if another stock with same product id already exists
        existing_stock = session.query(Product).filter_by(product_id=data["product_id"]).filter(Stock.stock_id != stockId).first()
        if existing_stock:
            return jsonify({"error": "Conflict", "message": "Stock with this product id already exists"}), 409

        stock.product_id = data["product_id"]
        stock.available_quantity = data["available_quantity"]
        stock.cost_price = data["cost_price"]
        stock.selling_price = data["selling_price"]
        session.commit()

        result = {
            "stock_id": stock.stock_id,
            "product_id": stock.product_id,
            "available_quantity": stock.available_quantity,
            "cost_price": stock.cost_price,
            "selling_price": stock.selling_price
        }
        return jsonify(result), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Failed to update stock", "message": str(e)}), 500
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
    app.run(debug=True ,port=2004)