from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.conf import settings

import requests
from bs4 import BeautifulSoup as bs
import re


# =========================
# TOP ARTISTS
# =========================
def top_artists():
    url = "https://spotify-scraper.p.rapidapi.com/v1/chart/artists/top"

    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    artists_info = []

    if "artists" in data:
        for artist in data["artists"]:
            name = artist.get("name", "No Name")
            avatar_url = artist.get("visuals", {}).get("avatar", [{}])[0].get("url", "")
            artist_id = artist.get("id", "")

            artists_info.append((name, avatar_url, artist_id))

    return artists_info


# =========================
# TOP TRACKS
# =========================
def top_tracks():
    url = "https://spotify-scraper.p.rapidapi.com/v1/chart/tracks/top"

    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    track_details = []

    if "tracks" in data:
        for track in data["tracks"][:18]:

            track_details.append({
                "id": track["id"],
                "name": track["name"],
                "artist": track["artists"][0]["name"] if track["artists"] else "",
                "cover_url": track["album"]["cover"][0]["url"] if track["album"]["cover"] else "",
            })

    return track_details


# =========================
# AUDIO DETAILS
# =========================
def get_audio_details(query):
    url = "https://spotify-scraper.p.rapidapi.com/v1/track/download"

    querystring = {"track": query}

    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    audio_details = []

    if response.status_code == 200:
        data = response.json()

        try:
            audio_list = data["youtubeVideo"]["audio"]
            if audio_list:
                audio_details.append(audio_list[0]["url"])
                audio_details.append(audio_list[0]["durationText"])
        except:
            pass

    return audio_details


# =========================
# TRACK IMAGE SCRAPING
# =========================
def get_track_image(track_id, track_name):
    url = "https://open.spotify.com/track/" + track_id

    r = requests.get(url)
    soup = bs(r.content, "html.parser")

    img = soup.find("img", {"alt": track_name})

    if img and img.get("srcset"):
        match = re.search(r"(https:\/\/i\.scdn\.co\/image\/[a-zA-Z0-9]+)", img["srcset"])
        if match:
            return match.group(1)

    return ""


# =========================
# MUSIC PAGE
# =========================
def music(request, pk):
    track_id = pk

    url = "https://spotify-scraper.p.rapidapi.com/v1/track/metadata"

    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "spotify-scraper.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params={"trackId": track_id})

    context = {}

    if response.status_code == 200:
        data = response.json()

        track_name = data.get("name", "")
        artist = data.get("artists", [{}])[0].get("name", "")

        audio = get_audio_details(track_name + artist)

        context = {
            "track_name": track_name,
            "artist_name": artist,
            "audio_url": audio[0] if len(audio) > 0 else "",
            "duration_text": audio[1] if len(audio) > 1 else "",
            "track_image": get_track_image(track_id, track_name),
        }

    return render(request, "music.html", context)


# =========================
# HOME PAGE
# =========================
@login_required(login_url="login")
def index(request):
    tracks = top_tracks()

    return render(request, "index.html", {
        "artists_info": top_artists(),
        "first_six_tracks": tracks[:6],
        "second_six_tracks": tracks[6:12],
        "third_six_tracks": tracks[12:18],
    })


# =========================
# SEARCH
# =========================
def search(request):
    track_list = []
    search_results_count = 0

    if request.method == "POST":
        query = request.POST["search_query"]

        url = "https://spotify-scraper.p.rapidapi.com/v1/search"

        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "spotify-scraper.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params={"term": query, "type": "track"})

        if response.status_code == 200:
            data = response.json()

            search_results_count = data["tracks"]["totalCount"]

            for track in data["tracks"]["items"]:
                track_list.append({
                    "track_name": track["name"],
                    "artist_name": track["artists"][0]["name"],
                    "duration": track["durationText"],
                    "trackid": track["id"],
                    "track_image": get_track_image(track["id"], track["name"]) or
                    "https://imgv3.fotor.com/images/blog-richtext-image/music-of-the-spheres-album-cover.jpg",
                })

    return render(request, "search.html", {
        "search_results_count": search_results_count,
        "track_list": track_list,
    })


# =========================
# PROFILE PAGE
# =========================
def profile(request, pk):
    url = "https://spotify-scraper.p.rapidapi.com/v1/artist/overview"

    response = requests.get(
        url,
        headers={
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": "spotify-scraper.p.rapidapi.com"
        },
        params={"artistId": pk}
    )

    if response.status_code != 200:
        return render(request, "profile.html", {})

    data = response.json()

    top_tracks = []

    for t in data["discography"]["topTracks"]:
        top_tracks.append({
            "id": t["id"],
            "name": t["name"],
            "durationText": t["durationText"],
            "playCount": t["playCount"],
            "track_image": get_track_image(str(t["id"]), t["name"]),
        })

    return render(request, "profile.html", {
        "name": data["name"],
        "monthlyListeners": data["stats"]["monthlyListeners"],
        "headerUrl": data["visuals"]["header"][0]["url"],
        "topTracks": top_tracks,
    })


# =========================
# AUTH
# =========================
def login(request):
    if request.method == "POST":
        user = auth.authenticate(
            username=request.POST["username"],
            password=request.POST["password"]
        )

        if user:
            auth.login(request, user)
            return redirect("index")

        messages.info(request, "Invalid credentials")
        return redirect("login")

    return render(request, "login.html")


def signup(request):
    if request.method == "POST":
        email = request.POST["email"]
        username = request.POST["username"]
        password = request.POST["password"]
        password2 = request.POST["password2"]

        if password != password2:
            messages.info(request, "Passwords not matching")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.info(request, "Username taken")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.info(request, "Email taken")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        auth.login(request, user)
        return redirect("index")

    return render(request, "signup.html")


# =========================
# LOGOUT
# =========================
@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    return redirect("login")