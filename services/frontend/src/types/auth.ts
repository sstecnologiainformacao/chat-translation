export type LoginRequest = {
  username: string;
  password: string;
};

export type LoginResponse = {
  token: string;
};

export type RegisterRequest = {
  username: string;
  password: string;
  language: string;
  nickname: string;
};

export type RegisterResponse = {
  username: string;
};
