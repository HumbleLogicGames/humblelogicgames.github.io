---
layout: page
title: Humble Logic Games
permalink: /
---

**Humble Logic Games** is an independent mobile game studio founded in 2020. We make free, family-friendly puzzle and card games for Android and iOS: tile matching, sudoku, solitaire, mahjong and more. Every game is designed to be quick to pick up, relaxing to play, and fair to everyone.

Contact: [humblelogicgames@gmail.com](mailto:humblelogicgames@gmail.com)

## Our games

<div class="hlg-games">
{% for g in site.data.games %}
  <div class="hlg-game">
    <img src="{{ '/assets/icons/' | append: g.slug | append: '.png' | relative_url }}" alt="{{ g.name }} icon" width="72" height="72">
    <div>
      <strong>{% if g.page %}<a href="{{ g.page | relative_url }}">{{ g.name }}</a>{% else %}{{ g.name }}{% endif %}</strong><br>
      {{ g.desc }}<br>
      <a href="https://play.google.com/store/apps/details?id={{ g.package }}">Google Play</a>
    </div>
  </div>
{% endfor %}
</div>

## Google account sign-in in our games

Some of our games let you sign in with **Google Play Games Services**. Signing in is optional and is used only to:

- show your achievements and leaderboards,
- save your game progress to the cloud so you can continue on another device,
- restore that progress when you reinstall the game.

We do not use your Google account for anything else, and you can play every game without signing in. See our [Privacy Policy]({{ '/docs/privacypolicy' | relative_url }}) and [Terms of Service]({{ '/docs/termsofservice' | relative_url }}) for details.

<style>
.hlg-games{display:flex;flex-direction:column;gap:14px;margin:12px 0 24px}
.hlg-game{display:flex;gap:14px;align-items:flex-start}
.hlg-game img{border-radius:16px;flex:none}
</style>
