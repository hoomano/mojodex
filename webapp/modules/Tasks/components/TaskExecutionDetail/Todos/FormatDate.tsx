import moment from "moment";

export function formatDateString(date: string) {
  const now = moment();
  const today = moment().startOf("day");
  const tomorrow = moment().add(1, "day").startOf("day");
  const parsedDate = moment(date).local();

  if (!parsedDate.isValid()) {
    return date;
  }

  const isToday = now.isSame(parsedDate, "day");
  if (isToday) {
    return "Today";
  }

  const isTomorrow = tomorrow.isSame(parsedDate, "day");
  if (isTomorrow) {
    return "Tomorrow";
  }

  if (parsedDate.year() === today.year()) {
    return parsedDate.format("D MMM");
  } else {
    return parsedDate.format("D MMM YYYY");
  }
}
