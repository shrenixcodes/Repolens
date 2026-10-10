import { Cart } from "../cart";
import { formatCurrency } from "../format";
import { Button } from "./Button";

export interface CartSummaryProps {
  cart: Cart;
  onCheckout: () => void;
}

export function CartSummary({ cart, onCheckout }: CartSummaryProps) {
  const total = cart.getTotal();
  return (
    <div>
      <p>
        {total.itemCount} items -- {formatCurrency(total.subtotalCents)}
      </p>
      <Button label="Checkout" onClick={onCheckout} />
    </div>
  );
}
