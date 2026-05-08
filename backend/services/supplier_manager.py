from backend.database.models import db, Supplier, SupplierIngredient, Ingredient

class SupplierManager:
    """Manage supplier relationships and purchase orders"""
    
    def __init__(self):
        pass
    
    def find_best_supplier(self, ingredient_id, quantity_needed):
        """
        Find the best supplier for an ingredient
        
        Criteria:
        1. Preferred suppliers first
        2. Lowest unit price
        3. Meets minimum order quantity
        
        Returns:
            dict with supplier info
        """
        # Get all suppliers for this ingredient
        supplier_options = db.session.query(
            Supplier, SupplierIngredient
        ).join(
            SupplierIngredient, Supplier.id == SupplierIngredient.supplier_id
        ).filter(
            SupplierIngredient.ingredient_id == ingredient_id
        ).all()
        
        if not supplier_options:
            return None
        
        # Filter by minimum quantity
        valid_suppliers = []
        for supplier, supplier_ing in supplier_options:
            if quantity_needed >= supplier_ing.minimum_quantity:
                valid_suppliers.append({
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name,
                    'unit_price': supplier_ing.unit_price,
                    'is_preferred': supplier_ing.is_preferred,
                    'delivery_days': supplier.delivery_days,
                    'total_cost': quantity_needed * supplier_ing.unit_price
                })
        
        if not valid_suppliers:
            return None
        
        # Sort: preferred first, then by price
        valid_suppliers.sort(
            key=lambda x: (not x['is_preferred'], x['unit_price'])
        )
        
        return valid_suppliers[0]
    
    def generate_purchase_order(self, shopping_list):
        """
        Generate purchase orders grouped by supplier
        
        Args:
            shopping_list: list of items to order
        
        Returns:
            dict of purchase orders per supplier
        """
        purchase_orders = {}
        
        for item in shopping_list:
            ingredient = db.session.query(Ingredient).filter_by(
                name=item['ingredient']
            ).first()
            
            if not ingredient:
                continue
            
            # Find best supplier
            supplier_info = self.find_best_supplier(
                ingredient.id, 
                item['quantity']
            )
            
            if not supplier_info:
                # No supplier found
                if 'No Supplier' not in purchase_orders:
                    purchase_orders['No Supplier'] = {
                        'supplier_id': None,
                        'items': [],
                        'total_cost': 0
                    }
                
                purchase_orders['No Supplier']['items'].append({
                    'ingredient': item['ingredient'],
                    'quantity': item['quantity'],
                    'unit': item['unit']
                })
                continue
            
            # Group by supplier
            supplier_name = supplier_info['supplier_name']
            
            if supplier_name not in purchase_orders:
                purchase_orders[supplier_name] = {
                    'supplier_id': supplier_info['supplier_id'],
                    'delivery_days': supplier_info['delivery_days'],
                    'items': [],
                    'total_cost': 0
                }
            
            purchase_orders[supplier_name]['items'].append({
                'ingredient': item['ingredient'],
                'quantity': item['quantity'],
                'unit': item['unit'],
                'unit_price': supplier_info['unit_price'],
                'line_total': supplier_info['total_cost']
            })
            
            purchase_orders[supplier_name]['total_cost'] += supplier_info['total_cost']
        
        return purchase_orders
    
    def add_supplier(self, supplier_data):
        """Add new supplier"""
        supplier = Supplier(**supplier_data)
        db.session.add(supplier)
        db.session.commit()
        return supplier.id
    
    def link_supplier_ingredient(self, supplier_id, ingredient_id, unit_price, 
                                 minimum_quantity=0, is_preferred=False):
        """Link supplier to ingredient with pricing"""
        link = SupplierIngredient(
            supplier_id=supplier_id,
            ingredient_id=ingredient_id,
            unit_price=unit_price,
            minimum_quantity=minimum_quantity,
            is_preferred=is_preferred
        )
        db.session.add(link)
        db.session.commit()
        return link.id