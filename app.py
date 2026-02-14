from flask import Flask, request, render_template_string, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
import threading
import time

app = Flask(__name__)
CORS(app)

# Store download progress
download_status = {}

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Main HTML Template (SAME AS BEFORE - NO CHANGE)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Sat.ytdownloader - Premium YouTube Downloader</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="description" content="Download YouTube videos and audio in multiple qualities - Free, Fast & Safe">
    <meta name="theme-color" content="#000000">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            scroll-behavior: smooth;
        }
        
        body {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #000000;
            min-height: 100vh;
            color: #ffffff;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }
        
        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: 
                radial-gradient(ellipse at 20% 0%, rgba(255, 0, 0, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(255, 0, 0, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(20, 0, 0, 1) 0%, #000000 100%);
        }
        
        .bg-shapes {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }
        
        .shape {
            position: absolute;
            border-radius: 50%;
            opacity: 0.1;
        }
        
        .shape-1 {
            width: 400px;
            height: 400px;
            background: linear-gradient(135deg, #ff0000, #880000);
            top: -100px;
            right: -100px;
            animation: float 8s ease-in-out infinite;
        }
        
        .shape-2 {
            width: 300px;
            height: 300px;
            background: linear-gradient(135deg, #ff0000, #440000);
            bottom: -50px;
            left: -50px;
            animation: float 10s ease-in-out infinite reverse;
        }
        
        .shape-3 {
            width: 200px;
            height: 200px;
            background: #ff0000;
            top: 50%;
            left: 50%;
            animation: pulse 5s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-30px) rotate(5deg); }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.05; }
            50% { transform: scale(1.2); opacity: 0.1; }
        }
        
        /* Header */
        .header {
            text-align: center;
            padding: 50px 20px 30px;
            position: relative;
        }
        
        .logo-container {
            display: inline-block;
            position: relative;
        }
        
        .logo-glow {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 120px;
            height: 120px;
            background: radial-gradient(circle, rgba(255,0,0,0.3) 0%, transparent 70%);
            border-radius: 50%;
            filter: blur(20px);
            animation: glow 3s ease-in-out infinite;
        }
        
        @keyframes glow {
            0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
        }
        
        .logo-emoji {
            font-size: 70px;
            display: block;
            margin-bottom: 20px;
            position: relative;
            filter: drop-shadow(0 0 30px rgba(255, 0, 0, 0.5));
            animation: bounce 2s ease-in-out infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .logo {
            font-size: 38px;
            font-weight: 800;
            background: linear-gradient(135deg, #ff0000 0%, #ff4444 50%, #ff0000 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shine 3s linear infinite;
            letter-spacing: -1px;
            position: relative;
        }
        
        @keyframes shine {
            to { background-position: 200% center; }
        }
        
        .tagline {
            color: #666666;
            font-size: 14px;
            font-weight: 400;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 15px;
        }
        
        .premium-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, #ff0000, #cc0000);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-top: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Main Container */
        .main-container {
            max-width: 650px;
            margin: 0 auto;
            padding: 0 20px 40px;
        }
        
        /* Card Style */
        .card {
            background: linear-gradient(165deg, #141414 0%, #0a0a0a 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 28px;
            padding: 35px;
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
            box-shadow: 
                0 25px 80px rgba(0, 0, 0, 0.6),
                0 0 0 1px rgba(255, 255, 255, 0.05),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #ff0000, #ff4444, #ff0000);
            background-size: 200% 100%;
            animation: gradient 3s linear infinite;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }
        
        .card::after {
            content: '';
            position: absolute;
            top: 4px;
            left: 20%;
            right: 20%;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,0,0,0.3), transparent);
        }
        
        /* Input Section */
        .input-section {
            margin-bottom: 25px;
        }
        
        .input-label {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 15px;
            font-size: 15px;
            color: #ffffff;
            font-weight: 500;
        }
        
        .input-label-icon {
            font-size: 20px;
        }
        
        .input-wrapper {
            position: relative;
        }
        
        .url-input {
            width: 100%;
            padding: 20px 55px 20px 22px;
            border: 2px solid #2a2a2a;
            border-radius: 16px;
            font-size: 16px;
            background: #0d0d0d;
            color: #ffffff;
            font-family: inherit;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .url-input:focus {
            outline: none;
            border-color: #ff0000;
            box-shadow: 
                0 0 0 4px rgba(255, 0, 0, 0.1),
                0 0 30px rgba(255, 0, 0, 0.15);
        }
        
        .url-input::placeholder {
            color: #444444;
        }
        
        .paste-btn {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: linear-gradient(135deg, #ff0000, #cc0000);
            border: none;
            border-radius: 12px;
            padding: 12px 14px;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .paste-btn:hover {
            transform: translateY(-50%) scale(1.05);
            box-shadow: 0 5px 20px rgba(255, 0, 0, 0.4);
        }
        
        .paste-btn:active {
            transform: translateY(-50%) scale(0.95);
        }
        
        /* Thumbnail Preview */
        .thumbnail-section {
            display: none;
            margin: 30px 0;
            animation: slideUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .thumbnail-section.active {
            display: block;
        }
        
        @keyframes slideUp {
            from { 
                opacity: 0; 
                transform: translateY(30px); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0); 
            }
        }
        
        .thumbnail-card {
            background: #0d0d0d;
            border-radius: 20px;
            padding: 20px;
            border: 2px solid #1a1a1a;
            position: relative;
        }
        
        .thumbnail-wrapper {
            position: relative;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5);
        }
        
        .thumbnail-img {
            width: 100%;
            height: auto;
            display: block;
            transition: transform 0.5s;
        }
        
        .thumbnail-wrapper:hover .thumbnail-img {
            transform: scale(1.02);
        }
        
        .thumbnail-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(0deg, rgba(0,0,0,0.8) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .thumbnail-badge {
            position: absolute;
            top: 15px;
            left: 15px;
            background: linear-gradient(135deg, #00c853, #00e676);
            color: #000;
            padding: 8px 16px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 15px rgba(0, 200, 83, 0.4);
        }
        
        .thumbnail-play {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 70px;
            height: 70px;
            background: rgba(255, 0, 0, 0.9);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            box-shadow: 0 10px 40px rgba(255, 0, 0, 0.5);
            transition: all 0.3s;
        }
        
        .thumbnail-wrapper:hover .thumbnail-play {
            transform: translate(-50%, -50%) scale(1.1);
        }
        
        .video-info {
            margin-top: 18px;
            text-align: center;
        }
        
        .video-title {
            color: #ffffff;
            font-size: 15px;
            font-weight: 500;
            line-height: 1.5;
        }
        
        .video-ready {
            color: #00c853;
            font-size: 13px;
            margin-top: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        
        /* Quality Section */
        .quality-section {
            display: none;
            margin-top: 30px;
            animation: fadeIn 0.5s ease;
        }
        
        .quality-section.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .section-icon {
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #ff0000, #cc0000);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 5px 20px rgba(255, 0, 0, 0.3);
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
        }
        
        .section-subtitle {
            font-size: 13px;
            color: #666666;
            margin-top: 2px;
        }
        
        /* Download Grid */
        .download-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
        }
        
        .download-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 22px 15px;
            border: 2px solid #222222;
            border-radius: 18px;
            background: linear-gradient(165deg, #151515 0%, #0a0a0a 100%);
            color: #ffffff;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            text-decoration: none;
            position: relative;
            overflow: hidden;
        }
        
        .download-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.5s;
        }
        
        .download-btn:hover::before {
            left: 100%;
        }
        
        .download-btn:hover {
            border-color: #ff0000;
            transform: translateY(-5px);
            box-shadow: 
                0 15px 40px rgba(255, 0, 0, 0.2),
                0 0 0 1px rgba(255, 0, 0, 0.1);
        }
        
        .download-btn:active {
            transform: translateY(-2px);
        }
        
        .download-btn.video-btn:hover {
            background: linear-gradient(165deg, #200a0a 0%, #100505 100%);
        }
        
        .download-btn.audio-btn {
            border-color: #1a1a1a;
        }
        
        .download-btn.audio-btn:hover {
            border-color: #00c853;
            background: linear-gradient(165deg, #0a200a 0%, #051005 100%);
            box-shadow: 
                0 15px 40px rgba(0, 200, 83, 0.15),
                0 0 0 1px rgba(0, 200, 83, 0.1);
        }
        
        .btn-emoji {
            font-size: 32px;
            margin-bottom: 10px;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }
        
        .btn-quality {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        
        .btn-format {
            font-size: 11px;
            color: #666666;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }
        
        /* Divider */
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #333333, transparent);
            margin: 35px 0;
        }
        
        /* Audio Grid */
        .audio-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        
        /* Features */
        .features {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 35px;
        }
        
        .feature {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.03);
            padding: 12px 20px;
            border-radius: 30px;
            font-size: 13px;
            color: #888888;
            border: 1px solid rgba(255, 255, 255, 0.06);
            transition: all 0.3s;
        }
        
        .feature:hover {
            background: rgba(255, 0, 0, 0.05);
            border-color: rgba(255, 0, 0, 0.2);
            color: #ffffff;
        }
        
        .feature-icon {
            font-size: 18px;
        }
        
        /* How To Card */
        .how-to-card {
            background: linear-gradient(165deg, #0f0f0f 0%, #080808 100%);
        }
        
        .steps {
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        
        .step {
            display: flex;
            align-items: center;
            gap: 18px;
            padding: 18px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            transition: all 0.3s;
        }
        
        .step:hover {
            background: rgba(255, 0, 0, 0.03);
            border-color: rgba(255, 0, 0, 0.1);
        }
        
        .step-number {
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #ff0000, #cc0000);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            flex-shrink: 0;
        }
        
        .step-text {
            font-size: 14px;
            color: #cccccc;
            line-height: 1.5;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: #444444;
            font-size: 13px;
        }
        
        .footer-brand {
            color: #ff0000;
            font-weight: 700;
        }
        
        .footer-links {
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 25px;
        }
        
        .footer-link {
            color: #555555;
            text-decoration: none;
            font-size: 12px;
            transition: color 0.3s;
        }
        
        .footer-link:hover {
            color: #ff0000;
        }
        
        .footer-heart {
            color: #ff0000;
            animation: heartbeat 1.5s infinite;
        }
        
        @keyframes heartbeat {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
        
        /* Loading State */
        .loading-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .loading-overlay.active {
            display: flex;
        }
        
        .loading-content {
            text-align: center;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid #222222;
            border-top-color: #ff0000;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 25px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: #ffffff;
            font-size: 18px;
            font-weight: 500;
        }
        
        .loading-subtext {
            color: #666666;
            font-size: 14px;
            margin-top: 10px;
        }
        
        /* ========== RESPONSIVE DESIGN ========== */
        
        /* Tablet */
        @media (max-width: 768px) {
            .header {
                padding: 40px 15px 25px;
            }
            
            .logo-emoji {
                font-size: 55px;
            }
            
            .logo {
                font-size: 30px;
            }
            
            .card {
                padding: 28px 22px;
                border-radius: 22px;
            }
            
            .download-grid {
                gap: 12px;
            }
            
            .audio-grid {
                gap: 10px;
            }
        }
        
        /* Mobile */
        @media (max-width: 550px) {
            .header {
                padding: 30px 15px 20px;
            }
            
            .logo-emoji {
                font-size: 45px;
                margin-bottom: 15px;
            }
            
            .logo {
                font-size: 24px;
            }
            
            .tagline {
                font-size: 11px;
                letter-spacing: 2px;
            }
            
            .premium-badge {
                font-size: 10px;
                padding: 5px 12px;
            }
            
            .main-container {
                padding: 0 15px 30px;
            }
            
            .card {
                padding: 22px 18px;
                border-radius: 18px;
                margin-bottom: 18px;
            }
            
            .input-label {
                font-size: 14px;
            }
            
            .url-input {
                padding: 16px 50px 16px 16px;
                font-size: 14px;
                border-radius: 14px;
            }
            
            .paste-btn {
                padding: 10px 12px;
                font-size: 16px;
            }
            
            .thumbnail-card {
                padding: 15px;
            }
            
            .thumbnail-play {
                width: 55px;
                height: 55px;
                font-size: 22px;
            }
            
            .section-header {
                margin-bottom: 15px;
                padding-bottom: 12px;
            }
            
            .section-icon {
                width: 38px;
                height: 38px;
                font-size: 18px;
            }
            
            .section-title {
                font-size: 17px;
            }
            
            .download-grid {
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            
            .download-btn {
                padding: 18px 12px;
                border-radius: 14px;
            }
            
            .btn-emoji {
                font-size: 26px;
                margin-bottom: 8px;
            }
            
            .btn-quality {
                font-size: 15px;
            }
            
            .btn-format {
                font-size: 9px;
            }
            
            .audio-grid {
                grid-template-columns: 1fr 1fr 1fr;
                gap: 8px;
            }
            
            .divider {
                margin: 25px 0;
            }
            
            .features {
                gap: 8px;
                margin-top: 25px;
            }
            
            .feature {
                padding: 10px 14px;
                font-size: 11px;
            }
            
            .step {
                padding: 14px;
                gap: 14px;
            }
            
            .step-number {
                width: 38px;
                height: 38px;
                font-size: 15px;
            }
            
            .step-text {
                font-size: 13px;
            }
        }
        
        /* Very Small Phones */
        @media (max-width: 380px) {
            .logo {
                font-size: 20px;
            }
            
            .logo-emoji {
                font-size: 40px;
            }
            
            .card {
                padding: 18px 14px;
            }
            
            .download-grid {
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            
            .audio-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .btn-emoji {
                font-size: 22px;
            }
            
            .btn-quality {
                font-size: 13px;
            }
        }
        
        /* Download Progress */
        .download-progress {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .download-progress.active {
            display: block;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #222;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff0000, #ff4444);
            border-radius: 4px;
            transition: width 0.3s;
            width: 0%;
        }
        
        .progress-text {
            color: #888;
            font-size: 12px;
            text-align: center;
        }
    </style>
</head>
<body>
    <!-- Background -->
    <div class="bg-animation"></div>
    <div class="bg-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-content">
            <div class="spinner"></div>
            <p class="loading-text">⬇️ Preparing Download...</p>
            <p class="loading-subtext">Please wait, this may take a moment</p>
        </div>
    </div>
    
    <!-- Header -->
    <header class="header">
        <div class="logo-container">
            <div class="logo-glow"></div>
            <span class="logo-emoji">🎬</span>
        </div>
        <h1 class="logo">Sat.ytdownloader</h1>
        <p class="tagline">✨ Premium YouTube Downloader ✨</p>
        <span class="premium-badge">⭐ 100% FREE</span>
    </header>
    
    <!-- Main Container -->
    <main class="main-container">
        
        <!-- Input Card -->
        <div class="card">
            <div class="input-section">
                <label class="input-label">
                    <span class="input-label-icon">🔗</span>
                    Paste YouTube Video or Shorts URL
                </label>
                <div class="input-wrapper">
                    <input 
                        type="text" 
                        id="urlInput" 
                        class="url-input" 
                        placeholder="https://www.youtube.com/watch?v=..." 
                        oninput="handleUrlInput(this.value)"
                        autocomplete="off"
                    >
                    <button type="button" class="paste-btn" onclick="pasteFromClipboard()" title="Paste from clipboard">
                        📋
                    </button>
                </div>
            </div>
            
            <!-- Thumbnail Preview -->
            <div class="thumbnail-section" id="thumbnailSection">
                <div class="thumbnail-card">
                    <div class="thumbnail-wrapper">
                        <img id="thumbnailImg" class="thumbnail-img" src="" alt="Video Thumbnail">
                        <div class="thumbnail-overlay"></div>
                        <span class="thumbnail-badge">✓ Found</span>
                        <div class="thumbnail-play">▶</div>
                    </div>
                    <div class="video-info">
                        <p class="video-title" id="videoTitle">Video ready for download</p>
                        <p class="video-ready">✅ Ready to download</p>
                    </div>
                </div>
            </div>
            
            <!-- Download Progress -->
            <div class="download-progress" id="downloadProgress">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p class="progress-text" id="progressText">Starting download...</p>
            </div>
            
            <!-- Video Quality Options -->
            <div class="quality-section" id="qualitySection">
                
                <div class="section-header">
                    <div class="section-icon">🎥</div>
                    <div>
                        <div class="section-title">Video (MP4)</div>
                        <div class="section-subtitle">Choose your preferred quality</div>
                    </div>
                </div>
                
                <div class="download-grid">
                    <button onclick="downloadVideo('best')" class="download-btn video-btn">
                        <span class="btn-emoji">🎬</span>
                        <span class="btn-quality">4K/Best</span>
                        <span class="btn-format">Highest Quality</span>
                    </button>
                    <button onclick="downloadVideo('1080')" class="download-btn video-btn">
                        <span class="btn-emoji">📺</span>
                        <span class="btn-quality">1080p</span>
                        <span class="btn-format">Full HD</span>
                    </button>
                    <button onclick="downloadVideo('720')" class="download-btn video-btn">
                        <span class="btn-emoji">💻</span>
                        <span class="btn-quality">720p</span>
                        <span class="btn-format">HD Ready</span>
                    </button>
                    <button onclick="downloadVideo('480')" class="download-btn video-btn">
                        <span class="btn-emoji">📱</span>
                        <span class="btn-quality">480p</span>
                        <span class="btn-format">Standard</span>
                    </button>
                    <button onclick="downloadVideo('360')" class="download-btn video-btn">
                        <span class="btn-emoji">📲</span>
                        <span class="btn-quality">360p</span>
                        <span class="btn-format">Low Data</span>
                    </button>
                    <button onclick="downloadVideo('240')" class="download-btn video-btn">
                        <span class="btn-emoji">💾</span>
                        <span class="btn-quality">240p</span>
                        <span class="btn-format">Minimum</span>
                    </button>
                </div>
                
                <div class="divider"></div>
                
                <div class="section-header">
                    <div class="section-icon" style="background: linear-gradient(135deg, #00c853, #00e676);">🎵</div>
                    <div>
                        <div class="section-title">Audio (MP3)</div>
                        <div class="section-subtitle">Extract audio only</div>
                    </div>
                </div>
                
                <div class="audio-grid">
                    <button onclick="downloadAudio('320')" class="download-btn audio-btn">
                        <span class="btn-emoji">🎧</span>
                        <span class="btn-quality">320kbps</span>
                        <span class="btn-format">Best</span>
                    </button>
                    <button onclick="downloadAudio('192')" class="download-btn audio-btn">
                        <span class="btn-emoji">🎵</span>
                        <span class="btn-quality">192kbps</span>
                        <span class="btn-format">High</span>
                    </button>
                    <button onclick="downloadAudio('128')" class="download-btn audio-btn">
                        <span class="btn-emoji">🎶</span>
                        <span class="btn-quality">128kbps</span>
                        <span class="btn-format">Normal</span>
                    </button>
                </div>
                
            </div>
            
            <!-- Features -->
            <div class="features">
                <span class="feature"><span class="feature-icon">⚡</span> Super Fast</span>
                <span class="feature"><span class="feature-icon">🔒</span> 100% Safe</span>
                <span class="feature"><span class="feature-icon">📱</span> All Devices</span>
                <span class="feature"><span class="feature-icon">🎬</span> Shorts Support</span>
            </div>
            
        </div>
        
        <!-- How to Use Card -->
        <div class="card how-to-card">
            <div class="section-header">
                <div class="section-icon">📖</div>
                <div>
                    <div class="section-title">How to Use</div>
                    <div class="section-subtitle">Just 4 simple steps</div>
                </div>
            </div>
            
            <div class="steps">
                <div class="step">
                    <div class="step-number">1️⃣</div>
                    <p class="step-text">Copy YouTube video or Shorts URL from YouTube</p>
                </div>
                <div class="step">
                    <div class="step-number">2️⃣</div>
                    <p class="step-text">Paste the URL in the input box above</p>
                </div>
                <div class="step">
                    <div class="step-number">3️⃣</div>
                    <p class="step-text">Check the thumbnail to verify it's the right video</p>
                </div>
                <div class="step">
                    <div class="step-number">4️⃣</div>
                    <p class="step-text">Select quality and click to download!</p>
                </div>
            </div>
        </div>
        
    </main>
    
    <!-- Footer -->
    <footer class="footer">
        <p>Made with <span class="footer-heart">❤️</span> by <span class="footer-brand">Sat.ytdownloader</span></p>
        <p style="margin-top: 10px; font-size: 11px;">🔒 For personal use only • We don't store any data</p>
        <div class="footer-links">
            <span class="footer-link">🌐 Works on all devices</span>
            <span class="footer-link">📱 Mobile friendly</span>
            <span class="footer-link">💻 Desktop ready</span>
        </div>
    </footer>
    
    <script>
        let currentVideoUrl = '';
        
        function handleUrlInput(url) {
            const thumbnailSection = document.getElementById('thumbnailSection');
            const qualitySection = document.getElementById('qualitySection');
            const thumbnailImg = document.getElementById('thumbnailImg');
            const videoTitle = document.getElementById('videoTitle');
            
            const videoId = extractVideoId(url);
            
            if (videoId) {
                currentVideoUrl = url;
                // Show thumbnail
                thumbnailImg.src = 'https://img.youtube.com/vi/' + videoId + '/maxresdefault.jpg';
                thumbnailImg.onerror = function() {
                    this.src = 'https://img.youtube.com/vi/' + videoId + '/hqdefault.jpg';
                };
                
                thumbnailSection.classList.add('active');
                qualitySection.classList.add('active');
                
                videoTitle.textContent = '✅ Video found and ready!';
            } else {
                thumbnailSection.classList.remove('active');
                qualitySection.classList.remove('active');
            }
        }
        
        function extractVideoId(url) {
            const patterns = [
                /(?:v=|\\/)([0-9A-Za-z_-]{11}).*/,
                /(?:embed\\/)([0-9A-Za-z_-]{11})/,
                /(?:shorts\\/)([0-9A-Za-z_-]{11})/,
                /(?:youtu\\.be\\/)([0-9A-Za-z_-]{11})/
            ];
            
            for (let pattern of patterns) {
                const match = url.match(pattern);
                if (match) return match[1];
            }
            return null;
        }
        
        async function pasteFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                document.getElementById('urlInput').value = text;
                handleUrlInput(text);
            } catch (err) {
                alert('📋 Please allow clipboard access or paste manually with Ctrl+V');
            }
        }
        
        function showLoading() {
            document.getElementById('loadingOverlay').classList.add('active');
        }
        
        function hideLoading() {
            document.getElementById('loadingOverlay').classList.remove('active');
        }
        
        function downloadVideo(quality) {
            if (!currentVideoUrl) {
                alert('Please paste a YouTube URL first!');
                return;
            }
            
            showLoading();
            
            // Create form and submit
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/download2';
            form.style.display = 'none';
            
            const urlInput = document.createElement('input');
            urlInput.name = 'url';
            urlInput.value = currentVideoUrl;
            form.appendChild(urlInput);
            
            const typeInput = document.createElement('input');
            typeInput.name = 'type';
            typeInput.value = 'video';
            form.appendChild(typeInput);
            
            const qualityInput = document.createElement('input');
            qualityInput.name = 'quality';
            qualityInput.value = quality;
            form.appendChild(qualityInput);
            
            document.body.appendChild(form);
            form.submit();
            
            setTimeout(hideLoading, 3000);
        }
        
        function downloadAudio(quality) {
            if (!currentVideoUrl) {
                alert('Please paste a YouTube URL first!');
                return;
            }
            
            showLoading();
            
            // Create form and submit
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/download2';
            form.style.display = 'none';
            
            const urlInput = document.createElement('input');
            urlInput.name = 'url';
            urlInput.value = currentVideoUrl;
            form.appendChild(urlInput);
            
            const typeInput = document.createElement('input');
            typeInput.name = 'type';
            typeInput.value = 'audio';
            form.appendChild(typeInput);
            
            const qualityInput = document.createElement('input');
            qualityInput.name = 'quality';
            qualityInput.value = quality;
            form.appendChild(qualityInput);
            
            document.body.appendChild(form);
            form.submit();
            
            setTimeout(hideLoading, 3000);
        }
        
        // Auto-paste on page load if URL is in clipboard
        window.addEventListener('load', function() {
            // Focus input on load
            document.getElementById('urlInput').focus();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return HTML_TEMPLATE

@app.route('/download2', methods=['POST'])
def download2():
    """NEW BROWSER DOWNLOAD ROUTE"""
    try:
        url = request.form['url']
        download_type = request.form.get('type', 'video')
        quality = request.form.get('quality', 'best')
        
        # Create unique filename
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        if download_type == 'audio':
            output_filename = f'audio_{unique_id}.mp3'
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'downloads/{output_filename}',
                'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'quiet': True,
                'no_warnings': True
            }
        else:
            output_filename = f'video_{unique_id}.mp4'
            if quality == 'best':
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                format_str = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best'
            
            ydl_opts = {
                'format': format_str,
                'outtmpl': f'downloads/{output_filename}',
                'merge_output_format': 'mp4',
                'ffmpeg_location': r'C:\ffmpeg\bin\ffmpeg.exe',
                'quiet': True,
                'no_warnings': True
            }
        
        # Download the file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_title = info.get('title', 'Video')
            
            # Clean filename for download
            safe_title = "".join(c for c in original_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            
            if download_type == 'audio':
                download_name = f'{safe_title}.mp3'
                # Check if file exists (might have different extension after conversion)
                if os.path.exists(f'downloads/{output_filename[:-4]}.mp3'):
                    file_path = f'downloads/{output_filename[:-4]}.mp3'
                else:
                    file_path = f'downloads/{output_filename}'
            else:
                download_name = f'{safe_title}.mp4'
                file_path = f'downloads/{output_filename}'
        
        # Check if file exists
        if os.path.exists(file_path):
            # Send file to browser for download
            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_name,
                mimetype='video/mp4' if download_type == 'video' else 'audio/mpeg'
            )
        else:
            return "Error: File not found after download", 404
            
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>❌ Error - Sat.ytdownloader</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #000;
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }}
                .error-box {{
                    background: #1a1a1a;
                    border: 2px solid #ff0000;
                    border-radius: 20px;
                    padding: 40px;
                    text-align: center;
                    max-width: 500px;
                }}
                h1 {{ color: #ff0000; }}
                a {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 15px 30px;
                    background: #ff0000;
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <h1>❌ Download Error</h1>
                <p>{str(e)}</p>
                <a href="/">⬅️ Go Back</a>
            </div>
        </body>
        </html>
        ''', 500

# Keep old download route for compatibility
@app.route('/download', methods=['POST'])
def download():
    # Redirect to new download route
    return download2()

if __name__ == '__main__':
    # Create downloads folder
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    print("")
    print("🎬 ========================================")
    print("🎬   Sat.ytdownloader is starting...")
    print("🎬 ========================================")
    print("")
    print("🌐 Open in browser: http://localhost:5000")
    print("")
    print("📱 For mobile access on same WiFi:")
    print("   Find your IP with: ipconfig")
    print("   Then open: http://YOUR_IP:5000")
    print("")
    print("⏹️  Press Ctrl+C to stop the server")
    print("")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    import qrcode

# Your IP address
ip = "192.168.43.123"  # Change to your IP
url = f"http://{ip}:5000"

# Generate QR
qr = qrcode.make(url)
qr.save("website_qr.png")
print(f"QR Code saved! URL: {url}")