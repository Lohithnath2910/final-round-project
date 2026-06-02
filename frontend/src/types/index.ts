export interface Event {
  event_id: string;
  property_id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface Booking {
  booking_id: string;
  property_id: string;
  room_type: string;
  checkin: string;
  checkout: string;
  status: string;
  amount_inr: number;
  source: string;
}

export interface AskResponse {
  answer: string;
  sql?: string | null;
  rows?: any[];
  citation?: string;
}