import datetime

from django.shortcuts import redirect, render

from djalaali.algo import is_leap_year, month_length, to_gregorian, to_jalaali
from djalaali.jdate import JalaliConfig, jdate
from djalaali.jdatetime import jdatetime

from .forms import ConvertForm, EventForm
from .models import Event


def index(request):
    form = EventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("index")
    return render(
        request,
        "events/index.html",
        {"form": form, "events": Event.objects.all()},
    )


def convert(request):
    form = ConvertForm(request.GET or None)
    today = jdate.today()
    ctx = {
        "form": form,
        "today": today,
        "now": jdatetime.now(),
        "months": [
            (m, JalaliConfig().get_month_name(m), month_length(today.year, m))
            for m in range(1, 13)
        ],
    }
    if form.is_valid():
        g = form.cleaned_data["date"]
        jd = jdate.fromgregorian(g)
        ctx["result"] = {
            "gregorian": g,
            "jalali": jd,
            "algo_to_jalaali": to_jalaali(g.year, g.month, g.day),
            "algo_to_gregorian": to_gregorian(jd.year, jd.month, jd.day),
            "leap": is_leap_year(jd.year),
            "weekday": jd.strftime("%A"),
            "plus_30": jd + datetime.timedelta(days=30),
            "days_since": today - jd,
            "parsed": jdate.strptime(jd.strftime("%d %B %Y"), "%d %B %Y"),
        }
    return render(request, "events/convert.html", ctx)
