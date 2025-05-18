from datetime import datetime
from flask import jsonify, request
from . import api_bp
from app.services.metal_service import MetalService

@api_bp.route('/metals/current', methods=['GET'])
def get_current_prices():
    """Get current prices for all metals, optionally in a specified currency."""
    try:
        target_currency = request.args.get('currency')
        prices = MetalService.get_current_prices(target_currency=target_currency)
        return jsonify({
            'status': 'success',
            'data': prices
        }), 200
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /metals/current: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': "Внутренняя ошибка сервера при получении текущих цен."
        }), 500

@api_bp.route('/metals/history', methods=['GET'])
def get_historical_prices():
    """Get historical prices for a specific metal."""
    try:
        metal = request.args.get('metal', '').upper()
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')

        if not all([metal, date_from_str, date_to_str]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: metal, date_from, date_to'
            }), 400

        try:
            date_from = datetime.fromisoformat(date_from_str)
            date_to = datetime.fromisoformat(date_to_str)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid date format. Use ISO format (YYYY-MM-DD)'
            }), 400

        prices = MetalService.get_historical_prices(metal, date_from, date_to)
        return jsonify({
            'status': 'success',
            'data': prices
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/metals/analysis', methods=['GET'])
def get_metal_analysis():
    """Get analysis for a specific metal."""
    try:
        metal = request.args.get('metal', '').upper()
        if not metal:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: metal'
            }), 400

        analysis = MetalService.analyze_metal(metal)
        if not analysis:
            return jsonify({
                'status': 'error',
                'message': f'No data available for metal: {metal}'
            }), 404

        return jsonify({
            'status': 'success',
            'data': analysis
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/metals/update', methods=['POST'])
def update_metal_prices():
    """Обновить цены на металлы."""
    try:
        MetalService.update_prices_from_parser()
        return jsonify({
            'status': 'success',
            'message': 'Цены на металлы успешно обновлены'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Закомментируем этот обработчик, чтобы использовался предыдущий, работающий с БД
# @api_bp.route('/metals/history', methods=['GET'])
# def get_historical_prices_from_mfd():
#     """Получить исторические цены по металлу и периоду с mfd.ru"""
#     try:
#         metal = request.args.get('metal', '').upper()
#         date_from = request.args.get('date_from', '')
#         date_to = request.args.get('date_to', '')
#         if not all([metal, date_from, date_to]):
#             return jsonify({'status': 'error', 'message': 'Необходимы параметры metal, date_from, date_to'}), 400
#         from app.services.alpha_vantage_service import MetalParserService
#         data = MetalParserService.get_historical_prices_from_mfd(metal, date_from, date_to)
#         return jsonify({'status': 'success', 'data': data}), 200
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500 