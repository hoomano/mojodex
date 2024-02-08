const fs = require("fs");

export default async function handler(req, res) {
  try {
    if (req.method === "POST") {
      const { body } = req;
      const { fileJson, lang } = body;

      const jsonString = JSON.stringify(fileJson, null, 2);

      const filePath = `public/locales/${lang}/dynamic.json`;

        const fileObj = await new Promise((res, rej) => {
          fs.writeFile(filePath, jsonString, "utf-8", (err) => {
            if (err) {
              console.error("Error writing file:", err);
              rej(err);
            } else {
              console.log("File successfully created:", filePath);
              res(filePath);
            }
          });
        });

      return res.status(200).json({ done: true });
    }
  } catch (error) {
    res.status(400).json({ error: "some error", error });
  }
}
