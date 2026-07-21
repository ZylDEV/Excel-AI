const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = {
  entry: "./src/index.tsx",
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "bundle.js",
    clean: true,
  },
  resolve: {
    extensions: [".ts", ".tsx", ".js", ".jsx"],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./public/index.html",
    }),
    new CopyWebpackPlugin({
      patterns: [
        { from: "public/assets", to: "assets", noErrorOnMissing: true },
        { from: "public/favicon.ico", to: "favicon.ico", noErrorOnMissing: true },
      ],
    }),
  ],
  devServer: {
    port: 3000,
    client: {
      overlay: false,
    },
    server: {
      type: "https",
      options: {
        cert: require("fs").readFileSync(
          path.resolve(process.env.HOME || process.env.USERPROFILE, ".office-addin-dev-certs", "localhost.crt")
        ),
        key: require("fs").readFileSync(
          path.resolve(process.env.HOME || process.env.USERPROFILE, ".office-addin-dev-certs", "localhost.key")
        ),
      },
    },
    hot: true,
    headers: {
      "Access-Control-Allow-Origin": "*",
    },
  },
};
