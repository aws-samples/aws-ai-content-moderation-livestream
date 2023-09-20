function ConvertUtcToLocal(utcTimestamp) {
  const utcDate = new Date(utcTimestamp);
  const localTimestamp = utcDate.toLocaleString();

  return localTimestamp;
}

function CalculateTimeDifference(targetEpoch) {
  const currentEpoch = Math.floor(Date.now() / 1000); // Current epoch time in seconds

  const timeDifference = currentEpoch - targetEpoch;

  const days = Math.floor(timeDifference / (60 * 60 * 24));
  const hours = Math.floor((timeDifference % (60 * 60 * 24)) / (60 * 60));
  const minutes = Math.floor((timeDifference % (60 * 60)) / 60);
  const seconds = Math.floor((timeDifference % (60)));

  let result = "";
  if (days > 0)
    result = `${days} days, `
  if (result.length > 0 || hours > 0)
    result = result + `${hours} hours, `
  if (result.length > 0 || minutes > 0)
    result = result + `${minutes} minutes, `
  if (result.length > 0 || seconds > 0)
    result = result + `${seconds} seconds`
  return result + ' ago';
}

export {ConvertUtcToLocal, CalculateTimeDifference};