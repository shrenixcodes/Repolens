export interface Product {
  id: string;
  name: string;
  priceCents: number;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export type CartTotal = {
  subtotalCents: number;
  itemCount: number;
};
