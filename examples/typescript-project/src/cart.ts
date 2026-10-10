import type { CartItem, CartTotal } from "./types";

export class Cart {
  private items: CartItem[] = [];

  addItem(item: CartItem): void {
    this.items.push(item);
  }

  removeProduct(productId: string): void {
    this.items = this.items.filter((item) => item.product.id !== productId);
  }

  getTotal(): CartTotal {
    let subtotalCents = 0;
    let itemCount = 0;
    for (const item of this.items) {
      subtotalCents += item.product.priceCents * item.quantity;
      itemCount += item.quantity;
    }
    return { subtotalCents, itemCount };
  }
}
