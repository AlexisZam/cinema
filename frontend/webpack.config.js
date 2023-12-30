import CssMinimizerWebpackPlugin from "css-minimizer-webpack-plugin";
import HtmlWebpackPlugin from "html-webpack-plugin";
import MiniCssExtractPlugin from "mini-css-extract-plugin";

const config = {
  cache: {
    buildDependencies: { config: [import.meta.filename] },
    memoryCacheUnaffected: true,
    type: "filesystem",
  },
  devServer: { allowedHosts: "all", webSocketServer: false },
  entry: "./src/index.ts",
  experiments: { cacheUnaffected: true },
  module: {
    rules: [
      { test: /\.css$/, use: [MiniCssExtractPlugin.loader, "css-loader"] },
      { test: /\.html$/, use: "html-loader" },
      {
        exclude: /node_modules/,
        test: /\.ts$/,
        use: { loader: "ts-loader" },
      },
    ],
  },
  optimization: {
    minimizer: [`...`, new CssMinimizerWebpackPlugin()],
    runtimeChunk: "single",
    splitChunks: {
      cacheGroups: {
        vendor: { chunks: "all", name: "vendors", test: /node_modules/ },
      },
      chunks: "all",
    },
  },
  // output: {
  //   environment: { asyncFunction: true },
  //   filename: "[name].[contenthash].js",
  // },
  plugins: [
    new HtmlWebpackPlugin({
      meta: {
        viewport: "width=device-width, initial-scale=1, shrink-to-fit=no",
      },
      scriptLoading: "module",
      title: "Cinema",
    }),
    new MiniCssExtractPlugin({ filename: "[contenthash].css" }),
  ],
  resolve: { extensions: [".ts"] },
};

export default config;
