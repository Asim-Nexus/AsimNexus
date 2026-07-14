/**
 * Webpack 5 Polyfill Overrides for react-scripts 5.0.1
 * 
 * react-scripts 5 uses Webpack 5 which removed automatic Node.js polyfills.
 * This config provides the necessary polyfills for dependencies that
 * expect Node.js built-in modules (crypto, buffer, stream, process, etc.).
 */
const webpack = require('webpack');

module.exports = function override(config) {
    // Provide Node.js polyfills for Webpack 5
    config.resolve.fallback = {
        ...config.resolve.fallback,
        crypto: require.resolve('crypto-browserify'),
        buffer: require.resolve('buffer/'),
        stream: require.resolve('stream-browserify'),
        process: require.resolve('process/browser.js'),
        vm: require.resolve('vm-browserify'),
        path: require.resolve('path-browserify'),
        os: require.resolve('os-browserify/browser.js'),
        fs: false,
        net: false,
        tls: false,
        child_process: false,
        http: require.resolve('stream-http'),
        https: require.resolve('https-browserify'),
        url: require.resolve('url/'),
        assert: require.resolve('assert/'),
        util: require.resolve('util/'),
        zlib: require.resolve('browserify-zlib'),
        querystring: require.resolve('querystring-es3'),
        string_decoder: require.resolve('string_decoder/'),
    };

    // Provide global process and Buffer
    config.plugins = [
        ...config.plugins,
        new webpack.ProvidePlugin({
            process: 'process/browser.js',
            Buffer: ['buffer', 'Buffer'],
        }),
    ];

    // Ignore source map warnings from polyfilled modules
    config.ignoreWarnings = [
        ...(config.ignoreWarnings || []),
        /Failed to parse source map/,
    ];

    return config;
};
