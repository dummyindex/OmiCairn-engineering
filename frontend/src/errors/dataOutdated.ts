export class DataOutdatedError extends Error {
  constructor(msg) {
    super(msg);
    console.log('msg', msg);
  }
}
