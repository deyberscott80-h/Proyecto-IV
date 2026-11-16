export interface Review {
  id: number;
  user_name: string;
  rating: number;
  comment: string;
  published_at: string;
  visible: boolean;
  response: string | null;
  replied_at: string | null;
}
export interface ReviewStats {
  total_comments: number;
  visible_comments: number;
  hidden_comments: number;
  answered_comments: number;
  average_rating: number;
}
export interface NewReview {
  user_name: string;
  rating: number;
  comment: string;
}
