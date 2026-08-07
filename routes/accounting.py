import csv, io
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Payment, Expense, Booking, Vendor
from helpers import admin_or_management, admin_only, get_or_404, parse_amount, kos_expense_query, safe_commit

accounting_bp = Blueprint("accounting", __name__, url_prefix="/accounting")

def get_month_range(year, month):
    if month == 12:
        return date(year, month, 1), date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month, 1), date(year + 1, month, 1) - timedelta(days=1)

@accounting_bp.route("/")
@admin_only
def index():
    tahun = request.args.get("tahun", date.today().year, type=int)
    bulan = request.args.get("bulan", date.today().month, type=int)

    start_date, end_date = get_month_range(tahun, bulan)

    pemasukan = db.session.query(db.func.sum(Payment.jumlah)).filter(
        Payment.status == "lunas",
        Payment.tanggal_bayar >= start_date,
        Payment.tanggal_bayar <= end_date,
    ).scalar() or 0

    pengeluaran = kos_expense_query(
        db.session.query(db.func.sum(Expense.jumlah)).filter(
            Expense.tanggal >= start_date,
            Expense.tanggal <= end_date,
        )
    ).scalar() or 0

    laba_rugi = pemasukan - pengeluaran

    daftar_pemasukan = Payment.query.filter(
        Payment.status == "lunas",
        Payment.tanggal_bayar >= start_date,
        Payment.tanggal_bayar <= end_date,
    ).order_by(Payment.tanggal_bayar.desc()).all()

    daftar_pengeluaran = kos_expense_query(
        Expense.query.filter(Expense.tanggal >= start_date, Expense.tanggal <= end_date)
    ).order_by(Expense.tanggal.desc()).all()

    # Batch: 12-month chart data in 2 queries instead of 24
    year_start = date(tahun, 1, 1)
    year_end = date(tahun, 12, 31)

    income_rows = db.session.query(
        db.func.to_char(Payment.tanggal_bayar, 'YYYY-MM').label('bulan'),
        db.func.sum(Payment.jumlah).label('total')
    ).filter(
        Payment.status == "lunas",
        Payment.tanggal_bayar >= year_start,
        Payment.tanggal_bayar <= year_end,
    ).group_by('bulan').all()
    income_map = {r.bulan: float(r.total) for r in income_rows}

    kos_id = session.get("kos_id")
    expense_q = db.session.query(
        db.func.to_char(Expense.tanggal, 'YYYY-MM').label('bulan'),
        db.func.sum(Expense.jumlah).label('total')
    ).filter(
        Expense.tanggal >= year_start,
        Expense.tanggal <= year_end,
    )
    if kos_id:
        expense_q = expense_q.filter(Expense.kos_id == kos_id)
    expense_rows = expense_q.group_by('bulan').all()
    expense_map = {r.bulan: float(r.total) for r in expense_rows}

    bulan_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    pemasukan_chart = []
    pengeluaran_chart = []
    for m in range(1, 13):
        key = f"{tahun}-{m:02d}"
        pemasukan_chart.append(income_map.get(key, 0))
        pengeluaran_chart.append(expense_map.get(key, 0))

    return render_template("accounting/index.html",
        tahun=tahun, bulan=bulan,
        pemasukan=pemasukan, pengeluaran=pengeluaran, laba_rugi=laba_rugi,
        daftar_pemasukan=daftar_pemasukan, daftar_pengeluaran=daftar_pengeluaran,
        bulan_names=bulan_names,
        pemasukan_chart=pemasukan_chart, pengeluaran_chart=pengeluaran_chart,
        selected_bulan=date(tahun, bulan, 1).strftime("%B"))

@accounting_bp.route("/pengeluaran/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah_pengeluaran():
    if request.method == "POST":
        jumlah, err = parse_amount(request.form.get("jumlah"))
        if err:
            flash(err, "danger")
            return render_template("accounting/expense_form.html", vendors=Vendor.query.order_by(Vendor.nama).all())

        expense = Expense(
            kos_id=session.get("kos_id"),
            kategori=request.form.get("kategori", "lainnya"),
            jumlah=jumlah,
            tanggal=datetime.strptime(request.form["tanggal"], "%Y-%m-%d").date() if request.form.get("tanggal") else date.today(),
            deskripsi=request.form.get("deskripsi"),
            vendor_id=request.form.get("vendor_id", type=int) or None,
        )
        db.session.add(expense)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Failed to add expense")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Pengeluaran berhasil dicatat.", "success")
        return redirect(url_for("accounting.index"))

    return render_template("accounting/expense_form.html", vendors=Vendor.query.order_by(Vendor.nama).all())

@accounting_bp.route("/pengeluaran/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit_pengeluaran(id):
    expense = get_or_404(Expense, id)

    if request.method == "POST":
        jumlah_val, err = parse_amount(request.form.get("jumlah"))
        if err:
            flash(err, "danger")
            return render_template("accounting/expense_form.html", expense=expense, vendors=Vendor.query.order_by(Vendor.nama).all())
        expense.jumlah = jumlah_val

        expense.kategori = request.form.get("kategori", "lainnya")
        expense.tanggal = datetime.strptime(request.form["tanggal"], "%Y-%m-%d").date() if request.form.get("tanggal") else date.today()
        expense.deskripsi = request.form.get("deskripsi")
        expense.vendor_id = request.form.get("vendor_id", type=int) or None
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Failed to update expense %s", id)
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Pengeluaran berhasil diperbarui.", "success")
        return redirect(url_for("accounting.index"))

    return render_template("accounting/expense_form.html", expense=expense, vendors=Vendor.query.order_by(Vendor.nama).all())

@accounting_bp.route("/pengeluaran/hapus/<int:id>", methods=["POST"])
@admin_or_management
def hapus_pengeluaran(id):
    expense = get_or_404(Expense, id)
    db.session.delete(expense)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to delete expense %s", id)
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Pengeluaran berhasil dihapus.", "success")
    return redirect(url_for("accounting.index"))

@accounting_bp.route("/laporan")
@admin_only
def laporan():
    tahun = request.args.get("tahun", date.today().year, type=int)

    # Batch: 12-month report in 2 queries instead of 24
    year_start = date(tahun, 1, 1)
    year_end = date(tahun, 12, 31)

    income_rows = db.session.query(
        db.func.to_char(Payment.tanggal_bayar, 'YYYY-MM').label('bulan'),
        db.func.sum(Payment.jumlah).label('total')
    ).filter(
        Payment.status == "lunas",
        Payment.tanggal_bayar >= year_start,
        Payment.tanggal_bayar <= year_end,
    ).group_by('bulan').all()
    income_map = {r.bulan: float(r.total) for r in income_rows}

    kos_id = session.get("kos_id")
    expense_q = db.session.query(
        db.func.to_char(Expense.tanggal, 'YYYY-MM').label('bulan'),
        db.func.sum(Expense.jumlah).label('total')
    ).filter(
        Expense.tanggal >= year_start,
        Expense.tanggal <= year_end,
    )
    if kos_id:
        expense_q = expense_q.filter(Expense.kos_id == kos_id)
    expense_rows = expense_q.group_by('bulan').all()
    expense_map = {r.bulan: float(r.total) for r in expense_rows}

    bulanan = []
    total_pemasukan = 0
    total_pengeluaran = 0
    for m in range(1, 13):
        key = f"{tahun}-{m:02d}"
        p = income_map.get(key, 0)
        pe = expense_map.get(key, 0)
        bulanan.append({
            "bulan": date(tahun, m, 1).strftime("%B"),
            "pemasukan": p,
            "pengeluaran": pe,
            "laba": p - pe,
        })
        total_pemasukan += p
        total_pengeluaran += pe

    return render_template("accounting/laporan.html",
        tahun=tahun, bulanan=bulanan,
        total_pemasukan=total_pemasukan, total_pengeluaran=total_pengeluaran,
        total_laba=total_pemasukan - total_pengeluaran)

@accounting_bp.route("/export/csv")
@admin_only
def export_csv():
    tahun = request.args.get("tahun", date.today().year, type=int)
    bulan = request.args.get("bulan", 0, type=int)
    jenis = request.args.get("jenis", "semua")
    kos_id = session.get("kos_id")

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Laporan Keuangan - Sistem Manajemen Kos", f"Periode: {tahun}" + (f"-{bulan:02d}" if bulan else "")])
    w.writerow([])

    if jenis in ("semua", "pemasukan"):
        w.writerow(["PEMASUKAN"])
        w.writerow(["Tanggal", "Penghuni", "Kamar", "Bulan", "Jumlah", "Metode", "Status"])
        q = Payment.query.join(Payment.booking).join(Booking.client).filter(Payment.status == "lunas")
        if bulan:
            s, e = get_month_range(tahun, bulan)
            q = q.filter(Payment.tanggal_bayar >= s, Payment.tanggal_bayar <= e)
        payments = q.all()
        for p in payments:
            w.writerow([
                p.tanggal_bayar.strftime("%d/%m/%Y") if p.tanggal_bayar else "-",
                p.booking.client.nama_lengkap, p.booking.room.nomor_kamar,
                p.bulan_dibayar_untuk, p.jumlah, p.metode_bayar, p.status
            ])
        w.writerow(["Total Pemasukan", "", "", "", sum(p.jumlah for p in payments)])
        w.writerow([])

    if jenis in ("semua", "pengeluaran"):
        w.writerow(["PENGELUARAN"])
        w.writerow(["Tanggal", "Kategori", "Deskripsi", "Jumlah"])
        eq = kos_expense_query(Expense.query)
        if bulan:
            s, e = get_month_range(tahun, bulan)
            eq = eq.filter(Expense.tanggal >= s, Expense.tanggal <= e)
        expenses = eq.all()
        for e in expenses:
            w.writerow([e.tanggal.strftime("%d/%m/%Y") if e.tanggal else "-", e.kategori, e.deskripsi or "", e.jumlah])
        w.writerow(["Total Pengeluaran", "", "", sum(e.jumlah for e in expenses)])
        w.writerow([])

    out.seek(0)
    return Response(
        out.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=laporan_{tahun}{'_'+str(bulan) if bulan else ''}.csv"}
    )
