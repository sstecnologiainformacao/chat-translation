export type LoginRequest = {
  username: string;
  password: string;
  nickname: string;
  language: string;
};

export type LoginResponse = {
  token: string;
};
