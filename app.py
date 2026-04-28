from flask import Flask, render_template, request, jsonify
import os
import random
import string
import database as db

app = Flask(__name__)

db.init_db()


def _gen_promo() -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=8))


@app.route('/')
def main():
    return render_template("index.html")


@app.route('/api/user_info')
def user_info():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    tcoins = db.get_tcoins(user_id)
    return jsonify({"tcoins": tcoins})


@app.route('/api/collect_promo', methods=['POST'])
def collect_promo():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    promo_type = data.get('promo_type', '')

    if not user_id:
        return jsonify({"success": False, "error": "user_id required"}), 400

    if not promo_type:
        return jsonify({"success": False, "error": "promo_type required"}), 400

    if not db.spend_tcoins(user_id, 1):
        tcoins = db.get_tcoins(user_id)
        return jsonify({"success": False, "error": "Недостаточно T-коинов", "tcoins": tcoins})

    code = _gen_promo()
    tcoins = db.get_tcoins(user_id)
    return jsonify({"success": True, "code": code, "tcoins": tcoins})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
