// Takes an array of promises and resolves them sequentially (in order); resolves to an array of the results
export function promiseSerial(promises: Promise<any>[]) {
  return promises.reduce(
    (promiseChain, currentTask) =>
      promiseChain.then((chainResults) =>
        currentTask.then((currentResult) => [...chainResults, currentResult]),
      ),
    Promise.resolve([]),
  );
}
